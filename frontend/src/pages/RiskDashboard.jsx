// FILE: frontend/src/pages/RiskDashboard.jsx
import React, { useState, useEffect } from 'react'
import { LineChart, Line, BarChart, Bar, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'

// Simple API calls without external library
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const apiCall = async (method, endpoint, data = null) => {
  try {
    const options = {
      method: method,
      headers: {
        'Content-Type': 'application/json',
      },
    }

    if (data) {
      options.body = JSON.stringify(data)
    }

    const response = await fetch(`${API_URL}${endpoint}`, options)
    
    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.detail || `HTTP ${response.status}`)
    }
    
    return await response.json()
  } catch (error) {
    console.error(`API Error [${method} ${endpoint}]:`, error.message)
    throw error
  }
}

export default function RiskDashboard() {
  const [activeTab, setActiveTab] = useState('dashboard')
  const [darkMode, setDarkMode] = useState(() => {
    const saved = localStorage.getItem('maatruDarkMode')
    return saved ? JSON.parse(saved) : false
  })
  const [mothers, setMothers] = useState([])
  const [analytics, setAnalytics] = useState({
    totalMothers: 0,
    highRiskCount: 0,
    moderateRiskCount: 0,
    lowRiskCount: 0,
    totalAssessments: 0
  })
  const [riskTrend, setRiskTrend] = useState([])
  const [ageDistribution, setAgeDistribution] = useState([])
  const [vitalStats, setVitalStats] = useState([])
  const [loading, setLoading] = useState(false)
  const [message, setMessage] = useState('')
  const [chartsLoading, setChartsLoading] = useState(false)

  // Save dark mode preference
  useEffect(() => {
    localStorage.setItem('maatruDarkMode', JSON.stringify(darkMode))
  }, [darkMode])

  // Register form state
  const [registerForm, setRegisterForm] = useState({
    name: '',
    phone: '',
    age: '',
    gravida: 'Gravida 1',
    parity: 'Parity 0',
    bmi: '',
    location: '',
    preferred_language: 'en',
    telegram_chat_id: ''
  })

  // Risk assessment form state
  const [assessmentForm, setAssessmentForm] = useState({
    mother_id: '',
    systolic_bp: '',
    diastolic_bp: '',
    heart_rate: '',
    blood_glucose: '',
    hemoglobin: '',
    proteinuria: 0,
    edema: 0,
    headache: 0,
    vision_changes: 0,
    epigastric_pain: 0,
    vaginal_bleeding: 0
  })

  const [riskResult, setRiskResult] = useState(null)
  const [expandedMother, setExpandedMother] = useState(null)

  // Fetch analytics only on mount and manual refresh
  useEffect(() => {
    fetchAnalyticsData()
  }, [])

  // Fetch mothers for dropdowns
  useEffect(() => {
    if (activeTab === 'risk-assessment' || activeTab === 'all-mothers') {
      fetchMothers()
    }
  }, [activeTab])

  const fetchAnalyticsData = async () => {
    try {
      setChartsLoading(true)
      const response = await apiCall('GET', '/analytics/dashboard')
      console.log('Analytics response:', response)
      setAnalytics({
        totalMothers: response.total_mothers || 0,
        highRiskCount: response.high_risk_count || 0,
        moderateRiskCount: response.moderate_risk_count || 0,
        lowRiskCount: response.low_risk_count || 0,
        totalAssessments: response.total_assessments || 0
      })

      // Fetch detailed analytics for charts
      await fetchDetailedAnalytics()
    } catch (error) {
      console.error('Failed to load analytics:', error.message)
      showMessage('Failed to refresh analytics', 'error')
    } finally {
      setChartsLoading(false)
    }
  }

  const fetchDetailedAnalytics = async () => {
    try {
      const mothersRes = await apiCall('GET', '/mothers')
      const mothersData = mothersRes.data || []

      // Fetch all assessments
      let allAssessments = []
      for (const mother of mothersData) {
        try {
          const res = await apiCall('GET', `/risk/mother/${mother.id}`)
          if (res.data) {
            allAssessments = [...allAssessments, ...res.data]
          }
        } catch (err) {
          console.log(`Could not fetch assessments for mother ${mother.id}`)
        }
      }

      // Age Distribution
      const ageGroups = {
        '15-20': 0,
        '20-25': 0,
        '25-30': 0,
        '30-35': 0,
        '35-40': 0,
        '40+': 0
      }

      mothersData.forEach(m => {
        if (m.age >= 15 && m.age < 20) ageGroups['15-20']++
        else if (m.age >= 20 && m.age < 25) ageGroups['20-25']++
        else if (m.age >= 25 && m.age < 30) ageGroups['25-30']++
        else if (m.age >= 30 && m.age < 35) ageGroups['30-35']++
        else if (m.age >= 35 && m.age < 40) ageGroups['35-40']++
        else ageGroups['40+']++
      })

      const ageData = Object.entries(ageGroups).map(([age, count]) => ({
        name: age,
        value: count
      }))
      setAgeDistribution(ageData)

      // Risk Trend (last 7 days)
      const sortedAssessments = allAssessments.sort((a, b) => 
        new Date(a.created_at) - new Date(b.created_at)
      )

      const dailyRisk = {}
      sortedAssessments.forEach(assessment => {
        const date = new Date(assessment.created_at).toLocaleDateString()
        if (!dailyRisk[date]) {
          dailyRisk[date] = { date, HIGH: 0, MODERATE: 0, LOW: 0 }
        }
        dailyRisk[date][assessment.risk_level]++
      })

      const riskData = Object.values(dailyRisk).slice(-7)
      setRiskTrend(riskData)

      // Vital Stats
      const vitals = {
        avgSystolic: 0,
        avgDiastolic: 0,
        avgHeartRate: 0,
        avgGlucose: 0,
        avgHemoglobin: 0
      }

      let systolicCount = 0, diastolicCount = 0, hrCount = 0, glucoseCount = 0, hbCount = 0

      allAssessments.forEach(assessment => {
        if (assessment.systolic_bp) {
          vitals.avgSystolic += assessment.systolic_bp
          systolicCount++
        }
        if (assessment.diastolic_bp) {
          vitals.avgDiastolic += assessment.diastolic_bp
          diastolicCount++
        }
        if (assessment.heart_rate) {
          vitals.avgHeartRate += assessment.heart_rate
          hrCount++
        }
        if (assessment.blood_glucose) {
          vitals.avgGlucose += assessment.blood_glucose
          glucoseCount++
        }
        if (assessment.hemoglobin) {
          vitals.avgHemoglobin += assessment.hemoglobin
          hbCount++
        }
      })

      const vitalData = [
        {
          name: 'Systolic BP',
          value: systolicCount > 0 ? Math.round(vitals.avgSystolic / systolicCount) : 0,
          normal: 120
        },
        {
          name: 'Diastolic BP',
          value: diastolicCount > 0 ? Math.round(vitals.avgDiastolic / diastolicCount) : 0,
          normal: 80
        },
        {
          name: 'Heart Rate',
          value: hrCount > 0 ? Math.round(vitals.avgHeartRate / hrCount) : 0,
          normal: 75
        },
        {
          name: 'Glucose',
          value: glucoseCount > 0 ? Math.round(vitals.avgGlucose / glucoseCount) : 0,
          normal: 100
        },
        {
          name: 'Hemoglobin',
          value: hbCount > 0 ? (vitals.avgHemoglobin / hbCount).toFixed(1) : 0,
          normal: 12
        }
      ]
      setVitalStats(vitalData)
    } catch (err) {
      console.error('Error fetching detailed analytics:', err)
    }
  }

  const fetchMothers = async () => {
    try {
      setLoading(true)
      const response = await apiCall('GET', '/mothers')
      const mothersData = response.data || []
      
      // Fetch assessments for each mother
      const mothersWithAssessments = await Promise.all(
        mothersData.map(async (mother) => {
          try {
            const assessResponse = await apiCall('GET', `/risk/mother/${mother.id}`)
            const assessments = assessResponse.data || []
            
            const latestAssessment = assessments.length > 0 ? assessments[0] : null
            
            return {
              ...mother,
              assessments: assessments,
              latestRisk: latestAssessment
            }
          } catch (e) {
            return {
              ...mother,
              assessments: [],
              latestRisk: null
            }
          }
        })
      )
      setMothers(mothersWithAssessments)
    } catch (error) {
      showMessage('Failed to load mothers: ' + error.message, 'error')
    } finally {
      setLoading(false)
    }
  }

  const handleRegisterSubmit = async (e) => {
    e.preventDefault()
    try {
      setLoading(true)

      const gravida = parseInt(registerForm.gravida.split(' ')[1], 10)
      const parity = parseInt(registerForm.parity.split(' ')[1], 10)

      const payload = {
        name: registerForm.name,
        phone: registerForm.phone,
        age: parseInt(registerForm.age, 10),
        gravida: gravida,
        parity: parity,
        bmi: parseFloat(registerForm.bmi),
        location: registerForm.location,
        preferred_language: registerForm.preferred_language,
        telegram_chat_id: registerForm.telegram_chat_id || null
      }

      console.log('Sending register payload:', payload)
      await apiCall('POST', '/mothers/register', payload)

      showMessage('✅ Mother registered successfully!', 'success')
      
      setRegisterForm({
        name: '',
        phone: '',
        age: '',
        gravida: 'Gravida 1',
        parity: 'Parity 0',
        bmi: '',
        location: '',
        preferred_language: 'en',
        telegram_chat_id: ''
      })

      fetchAnalyticsData()
    } catch (error) {
      showMessage('❌ Error: ' + error.message, 'error')
    } finally {
      setLoading(false)
    }
  }

  const handleAssessRisk = async (e) => {
    e.preventDefault()
    if (!assessmentForm.mother_id) {
      showMessage('Please select a mother', 'error')
      return
    }

    try {
      setLoading(true)

      const payload = {
        mother_id: assessmentForm.mother_id,
        systolic_bp: assessmentForm.systolic_bp ? parseInt(assessmentForm.systolic_bp, 10) : null,
        diastolic_bp: assessmentForm.diastolic_bp ? parseInt(assessmentForm.diastolic_bp, 10) : null,
        heart_rate: assessmentForm.heart_rate ? parseInt(assessmentForm.heart_rate, 10) : null,
        blood_glucose: assessmentForm.blood_glucose ? parseFloat(assessmentForm.blood_glucose) : null,
        hemoglobin: assessmentForm.hemoglobin ? parseFloat(assessmentForm.hemoglobin) : null,
        proteinuria: 0,
        edema: 0,
        headache: 0,
        vision_changes: 0,
        epigastric_pain: 0,
        vaginal_bleeding: 0
      }

      console.log('Sending assessment payload:', payload)
      const response = await apiCall('POST', '/risk/assess', payload)
      
      setRiskResult(response)
      showMessage('✅ Risk assessment completed!', 'success')
      
      // Clear form
      setAssessmentForm({
        mother_id: '',
        systolic_bp: '',
        diastolic_bp: '',
        heart_rate: '',
        blood_glucose: '',
        hemoglobin: '',
        proteinuria: 0,
        edema: 0,
        headache: 0,
        vision_changes: 0,
        epigastric_pain: 0,
        vaginal_bleeding: 0
      })
      
      fetchAnalyticsData()
    } catch (error) {
      showMessage('❌ Error: ' + error.message, 'error')
    } finally {
      setLoading(false)
    }
  }

  const handleRegisterChange = (e) => {
    const { name, value } = e.target
    setRegisterForm(prev => ({
      ...prev,
      [name]: value
    }))
  }

  const handleAssessmentChange = (e) => {
    const { name, value } = e.target
    
    if (name === 'mother_id') {
      setAssessmentForm({
        mother_id: value,
        systolic_bp: '',
        diastolic_bp: '',
        heart_rate: '',
        blood_glucose: '',
        hemoglobin: '',
        proteinuria: 0,
        edema: 0,
        headache: 0,
        vision_changes: 0,
        epigastric_pain: 0,
        vaginal_bleeding: 0
      })
      setRiskResult(null)
    } else {
      setAssessmentForm(prev => ({
        ...prev,
        [name]: value
      }))
    }
  }

  const showMessage = (text, type = 'info') => {
    setMessage({ text, type })
    setTimeout(() => setMessage(''), 4000)
  }

  const COLORS = {
    HIGH: '#ef4444',
    MODERATE: '#f59e0b',
    LOW: '#10b981',
    primary: '#6366f1',
    secondary: '#8b5cf6'
  }

  return (
    <div style={{ background: darkMode ? '#1a1a2e' : '#f0f4f8', minHeight: '100vh', padding: '20px', transition: 'background 0.3s' }}>
      <div style={{ maxWidth: '1400px', margin: '0 auto' }}>
        {/* Header with Dark Mode Toggle */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
          <div>
            <h1 style={{ color: darkMode ? '#fff' : '#1f2937', marginBottom: '8px' }}>🏥 MaatruRaksha AI</h1>
            <p style={{ color: darkMode ? '#9ca3af' : '#6b7280', marginBottom: '0' }}>Maternal Health Monitoring System</p>
          </div>
          <button
            onClick={() => setDarkMode(!darkMode)}
            style={{
              padding: '10px 16px',
              background: darkMode ? '#374151' : '#e5e7eb',
              border: 'none',
              borderRadius: '6px',
              cursor: 'pointer',
              fontWeight: '600',
              fontSize: '18px',
              transition: 'all 0.3s',
              boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
            }}
            title={darkMode ? 'Light Mode' : 'Dark Mode'}
          >
            {darkMode ? '☀️ Light' : '🌙 Dark'}
          </button>
        </div>

        {/* Notification */}
        {message && (
          <div style={{
            position: 'fixed',
            top: '20px',
            right: '20px',
            background: message.type === 'success' ? '#dcfce7' : message.type === 'error' ? '#fee2e2' : '#dbeafe',
            border: `2px solid ${message.type === 'success' ? '#86efac' : message.type === 'error' ? '#fecaca' : '#7dd3fc'}`,
            color: message.type === 'success' ? '#166534' : message.type === 'error' ? '#991b1b' : '#0c4a6e',
            padding: '16px 20px',
            borderRadius: '8px',
            boxShadow: '0 4px 6px rgba(0,0,0,0.1)',
            zIndex: 1000,
            fontSize: '14px',
            maxWidth: '400px'
          }}>
            {message.text}
          </div>
        )}

        {/* Tabs */}
        <div style={{
          display: 'flex',
          gap: '12px',
          marginBottom: '24px',
          background: darkMode ? '#262641' : 'white',
          padding: '8px',
          borderRadius: '8px',
          boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
          flexWrap: 'wrap',
          transition: 'background 0.3s'
        }}>
          {[
            { id: 'dashboard', label: '📊 Dashboard' },
            { id: 'register', label: '➕ Register' },
            { id: 'risk-assessment', label: '⚠️ Risk Assessment' },
            { id: 'all-mothers', label: '👥 All Mothers' }
          ].map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              style={{
                padding: '10px 20px',
                border: 'none',
                borderRadius: '6px',
                cursor: 'pointer',
                fontWeight: '600',
                fontSize: '14px',
                background: activeTab === tab.id ? '#667eea' : (darkMode ? '#374151' : '#f3f4f6'),
                color: activeTab === tab.id ? 'white' : (darkMode ? '#e5e7eb' : '#374151'),
                transition: 'all 0.3s'
              }}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Dashboard Tab - With Analytics */}
        {activeTab === 'dashboard' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
            {/* Top KPI Cards */}
            <div>
              <div style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                marginBottom: '20px',
                padding: '16px 20px',
                background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                borderRadius: '8px',
                color: 'white'
              }}>
                <h2 style={{ margin: 0, fontSize: '20px' }}>📈 Health Analytics</h2>
                <div style={{
                  background: 'rgba(255,255,255,0.2)',
                  padding: '10px 16px',
                  borderRadius: '6px',
                  fontSize: '16px',
                  fontWeight: '600'
                }}>
                  Total Mothers: <strong>{analytics.totalMothers}</strong>
                </div>
              </div>

              <div style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))',
                gap: '16px'
              }}>
                <div style={{
                  background: 'white',
                  padding: '20px',
                  borderRadius: '8px',
                  borderLeft: '4px solid #ef4444',
                  boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
                }}>
                  <div style={{ fontSize: '12px', color: '#6b7280', fontWeight: '600', marginBottom: '12px' }}>🔴 HIGH RISK</div>
                  <div style={{ fontSize: '40px', fontWeight: '700', color: '#ef4444' }}>{analytics.highRiskCount}</div>
                </div>

                <div style={{
                  background: 'white',
                  padding: '20px',
                  borderRadius: '8px',
                  borderLeft: '4px solid #f59e0b',
                  boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
                }}>
                  <div style={{ fontSize: '12px', color: '#6b7280', fontWeight: '600', marginBottom: '12px' }}>🟡 MODERATE RISK</div>
                  <div style={{ fontSize: '40px', fontWeight: '700', color: '#f59e0b' }}>{analytics.moderateRiskCount}</div>
                </div>

                <div style={{
                  background: 'white',
                  padding: '20px',
                  borderRadius: '8px',
                  borderLeft: '4px solid #10b981',
                  boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
                }}>
                  <div style={{ fontSize: '12px', color: '#6b7280', fontWeight: '600', marginBottom: '12px' }}>🟢 LOW RISK</div>
                  <div style={{ fontSize: '40px', fontWeight: '700', color: '#10b981' }}>{analytics.lowRiskCount}</div>
                </div>

                <div style={{
                  background: 'white',
                  padding: '20px',
                  borderRadius: '8px',
                  borderLeft: '4px solid #3b82f6',
                  boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
                }}>
                  <div style={{ fontSize: '12px', color: '#6b7280', fontWeight: '600', marginBottom: '12px' }}>📋 TOTAL ASSESSMENTS</div>
                  <div style={{ fontSize: '40px', fontWeight: '700', color: '#3b82f6' }}>{analytics.totalAssessments}</div>
                </div>
              </div>
            </div>

            {/* Charts Section */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
              {/* Risk Trend Chart */}
              <div style={{
                background: darkMode ? '#262641' : 'white',
                padding: '20px',
                borderRadius: '8px',
                boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
                transition: 'background 0.3s'
              }}>
                <h3 style={{ color: darkMode ? '#fff' : '#1f2937', marginBottom: '16px', fontSize: '16px', fontWeight: '600' }}>📊 Risk Trend (Last 7 Days)</h3>
                {riskTrend.length > 0 ? (
                  <ResponsiveContainer width="100%" height={300}>
                    <BarChart data={riskTrend} margin={{ top: 20, right: 30, left: 0, bottom: 60 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                      <XAxis dataKey="date" angle={-45} textAnchor="end" height={80} tick={{ fontSize: 12 }} />
                      <YAxis tick={{ fontSize: 12 }} />
                      <Tooltip contentStyle={{ backgroundColor: '#fff', border: '1px solid #e5e7eb', borderRadius: '8px' }} />
                      <Legend wrapperStyle={{ paddingTop: '20px' }} />
                      <Bar dataKey="HIGH" stackId="a" fill={COLORS.HIGH} name="High Risk" />
                      <Bar dataKey="MODERATE" stackId="a" fill={COLORS.MODERATE} name="Moderate Risk" />
                      <Bar dataKey="LOW" stackId="a" fill={COLORS.LOW} name="Low Risk" />
                    </BarChart>
                  </ResponsiveContainer>
                ) : (
                  <p style={{ color: '#6b7280', textAlign: 'center', padding: '40px 0' }}>No assessment data available</p>
                )}
              </div>

              {/* Age Distribution & Risk Distribution */}
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))', gap: '20px' }}>
                <div style={{
                  background: darkMode ? '#262641' : 'white',
                  padding: '20px',
                  borderRadius: '8px',
                  boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
                  transition: 'background 0.3s'
                }}>
                  <h3 style={{ color: darkMode ? '#fff' : '#1f2937', marginBottom: '16px', fontSize: '16px', fontWeight: '600' }}>👶 Age Distribution</h3>
                  {ageDistribution.some(d => d.value > 0) ? (
                    <ResponsiveContainer width="100%" height={300}>
                      <PieChart>
                        <Pie data={ageDistribution} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={80} label>
                          {ageDistribution.map((entry, index) => (
                            <Cell key={`cell-${index}`} fill={['#6366f1', '#8b5cf6', '#a855f7', '#d946ef', '#ec4899', '#f43f5e'][index % 6]} />
                          ))}
                        </Pie>
                        <Tooltip />
                      </PieChart>
                    </ResponsiveContainer>
                  ) : (
                    <p style={{ color: '#6b7280', textAlign: 'center', padding: '40px 0' }}>No data available</p>
                  )}
                </div>

                <div style={{
                  background: darkMode ? '#262641' : 'white',
                  padding: '20px',
                  borderRadius: '8px',
                  boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
                  transition: 'background 0.3s'
                }}>
                  <h3 style={{ color: darkMode ? '#fff' : '#1f2937', marginBottom: '16px', fontSize: '16px', fontWeight: '600' }}>⚠️ Overall Risk Distribution</h3>
                  {analytics && (analytics.highRiskCount + analytics.moderateRiskCount + analytics.lowRiskCount) > 0 ? (
                    <ResponsiveContainer width="100%" height={300}>
                      <PieChart>
                        <Pie
                          data={[
                            { name: 'High Risk', value: analytics.highRiskCount },
                            { name: 'Moderate Risk', value: analytics.moderateRiskCount },
                            { name: 'Low Risk', value: analytics.lowRiskCount }
                          ]}
                          dataKey="value"
                          cx="50%"
                          cy="50%"
                          outerRadius={80}
                          label
                        >
                          <Cell fill={COLORS.HIGH} />
                          <Cell fill={COLORS.MODERATE} />
                          <Cell fill={COLORS.LOW} />
                        </Pie>
                        <Tooltip />
                      </PieChart>
                    </ResponsiveContainer>
                  ) : (
                    <p style={{ color: '#6b7280', textAlign: 'center', padding: '40px 0' }}>No data available</p>
                  )}
                </div>
              </div>

              {/* Vital Signs Chart */}
              <div style={{
                background: darkMode ? '#262641' : 'white',
                padding: '20px',
                borderRadius: '8px',
                boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
                transition: 'background 0.3s'
              }}>
                <h3 style={{ color: darkMode ? '#fff' : '#1f2937', marginBottom: '16px', fontSize: '16px', fontWeight: '600' }}>💓 Average Vital Signs vs Normal Range</h3>
                {vitalStats.some(v => v.value > 0) ? (
                  <ResponsiveContainer width="100%" height={300}>
                    <BarChart data={vitalStats} margin={{ top: 20, right: 30, left: 0, bottom: 100 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                      <XAxis dataKey="name" angle={-45} textAnchor="end" height={120} tick={{ fontSize: 12 }} />
                      <YAxis tick={{ fontSize: 12 }} />
                      <Tooltip contentStyle={{ backgroundColor: '#fff', border: '1px solid #e5e7eb', borderRadius: '8px' }} />
                      <Legend wrapperStyle={{ paddingTop: '20px' }} />
                      <Bar dataKey="value" fill={COLORS.primary} name="Average Value" />
                      <Bar dataKey="normal" fill={COLORS.secondary} name="Normal Range" />
                    </BarChart>
                  </ResponsiveContainer>
                ) : (
                  <p style={{ color: '#6b7280', textAlign: 'center', padding: '40px 0' }}>No vital signs data available</p>
                )}
              </div>

              {/* Refresh Button */}
              <div style={{ display: 'flex', justifyContent: 'center', gap: '12px' }}>
                <button
                  onClick={fetchAnalyticsData}
                  disabled={chartsLoading}
                  style={{
                    padding: '12px 24px',
                    background: '#667eea',
                    color: 'white',
                    border: 'none',
                    borderRadius: '6px',
                    fontWeight: '600',
                    fontSize: '14px',
                    cursor: chartsLoading ? 'not-allowed' : 'pointer',
                    opacity: chartsLoading ? 0.6 : 1,
                    transition: 'all 0.3s'
                  }}
                >
                  {chartsLoading ? '⏳ Refreshing...' : '🔄 Refresh Analytics'}
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Register Tab */}
        {activeTab === 'register' && (
          <div style={{
            background: darkMode ? '#262641' : 'white',
            padding: '24px',
            borderRadius: '8px',
            boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
            maxWidth: '600px',
            transition: 'background 0.3s'
          }}>
            <h2 style={{ marginBottom: '8px', color: darkMode ? '#fff' : '#1f2937' }}>📝 Register Pregnant Mother</h2>
            <p style={{ color: darkMode ? '#9ca3af' : '#6b7280', marginBottom: '20px', fontSize: '14px' }}>Add a new mother to the system (data saved to Supabase)</p>

            <form onSubmit={handleRegisterSubmit}>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginBottom: '16px' }}>
                <div>
                  <label style={{ display: 'block', fontSize: '14px', fontWeight: '600', marginBottom: '6px', color: darkMode ? '#e5e7eb' : '#374151' }}>Full Name *</label>
                  <input type="text" name="name" placeholder="e.g., Priya Sharma" value={registerForm.name} onChange={handleRegisterChange} required style={{ width: '100%', padding: '10px 12px', border: `1px solid ${darkMode ? '#404854' : '#d1d5db'}`, borderRadius: '6px', fontSize: '14px', background: darkMode ? '#1a1a2e' : '#fff', color: darkMode ? '#fff' : '#000' }} />
                </div>
                <div>
                  <label style={{ display: 'block', fontSize: '14px', fontWeight: '600', marginBottom: '6px', color: '#374151' }}>📱 Phone Number *</label>
                  <input type="tel" name="phone" placeholder="9876543210" value={registerForm.phone} onChange={handleRegisterChange} required style={{ width: '100%', padding: '10px 12px', border: '1px solid #d1d5db', borderRadius: '6px', fontSize: '14px' }} />
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginBottom: '16px' }}>
                <div>
                  <label style={{ display: 'block', fontSize: '14px', fontWeight: '600', marginBottom: '6px', color: '#374151' }}>👤 Age (years) *</label>
                  <input type="number" name="age" placeholder="28" value={registerForm.age} onChange={handleRegisterChange} required style={{ width: '100%', padding: '10px 12px', border: '1px solid #d1d5db', borderRadius: '6px', fontSize: '14px' }} />
                </div>
                <div>
                  <label style={{ display: 'block', fontSize: '14px', fontWeight: '600', marginBottom: '6px', color: '#374151' }}>⚖️ BMI *</label>
                  <input type="number" name="bmi" placeholder="22.5" step="0.1" value={registerForm.bmi} onChange={handleRegisterChange} required style={{ width: '100%', padding: '10px 12px', border: '1px solid #d1d5db', borderRadius: '6px', fontSize: '14px' }} />
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginBottom: '16px' }}>
                <div>
                  <label style={{ display: 'block', fontSize: '14px', fontWeight: '600', marginBottom: '6px', color: '#374151' }}>Gravida</label>
                  <select name="gravida" value={registerForm.gravida} onChange={handleRegisterChange} style={{ width: '100%', padding: '10px 12px', border: '1px solid #d1d5db', borderRadius: '6px', fontSize: '14px' }}>
                    <option>Gravida 1</option>
                    <option>Gravida 2</option>
                    <option>Gravida 3</option>
                  </select>
                </div>
                <div>
                  <label style={{ display: 'block', fontSize: '14px', fontWeight: '600', marginBottom: '6px', color: '#374151' }}>Parity</label>
                  <select name="parity" value={registerForm.parity} onChange={handleRegisterChange} style={{ width: '100%', padding: '10px 12px', border: '1px solid #d1d5db', borderRadius: '6px', fontSize: '14px' }}>
                    <option>Parity 0</option>
                    <option>Parity 1</option>
                    <option>Parity 2</option>
                  </select>
                </div>
              </div>

              <div style={{ marginBottom: '16px' }}>
                <label style={{ display: 'block', fontSize: '14px', fontWeight: '600', marginBottom: '6px', color: '#374151' }}>📍 Location *</label>
                <input type="text" name="location" placeholder="e.g., Dharavi, Mumbai" value={registerForm.location} onChange={handleRegisterChange} required style={{ width: '100%', padding: '10px 12px', border: '1px solid #d1d5db', borderRadius: '6px', fontSize: '14px' }} />
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginBottom: '16px' }}>
                <div>
                  <label style={{ display: 'block', fontSize: '14px', fontWeight: '600', marginBottom: '6px', color: '#374151' }}>🌍 Preferred Language</label>
                  <select name="preferred_language" value={registerForm.preferred_language} onChange={handleRegisterChange} style={{ width: '100%', padding: '10px 12px', border: '1px solid #d1d5db', borderRadius: '6px', fontSize: '14px' }}>
                    <option value="en">English</option>
                    <option value="mr">Marathi</option>
                    <option value="hi">Hindi</option>
                  </select>
                </div>
                <div>
                  <label style={{ display: 'block', fontSize: '14px', fontWeight: '600', marginBottom: '6px', color: '#374151' }}>💬 Telegram Chat ID</label>
                  <input type="text" name="telegram_chat_id" placeholder="Optional: Chat ID" value={registerForm.telegram_chat_id} onChange={handleRegisterChange} style={{ width: '100%', padding: '10px 12px', border: '1px solid #d1d5db', borderRadius: '6px', fontSize: '14px' }} />
                </div>
              </div>

              <button type="submit" disabled={loading} style={{ width: '100%', padding: '12px', background: '#667eea', color: 'white', border: 'none', borderRadius: '6px', fontWeight: '600', fontSize: '14px', cursor: loading ? 'not-allowed' : 'pointer', opacity: loading ? 0.6 : 1 }}>
                {loading ? 'Registering...' : 'Register Mother'}
              </button>
            </form>
          </div>
        )}

        {/* Risk Assessment Tab */}
        {activeTab === 'risk-assessment' && (
          <div style={{
            background: 'white',
            padding: '24px',
            borderRadius: '8px',
            boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
            maxWidth: '600px'
          }}>
            <h2 style={{ marginBottom: '16px', color: '#1f2937' }}>⚕️ Risk Assessment</h2>

            <form onSubmit={handleAssessRisk}>
              <div style={{ marginBottom: '16px' }}>
                <label style={{ display: 'block', fontSize: '14px', fontWeight: '600', marginBottom: '6px', color: '#374151' }}>Select Mother *</label>
                <select name="mother_id" value={assessmentForm.mother_id} onChange={handleAssessmentChange} required style={{ width: '100%', padding: '10px 12px', border: '1px solid #d1d5db', borderRadius: '6px', fontSize: '14px' }}>
                  <option value="">Choose a mother...</option>
                  {mothers.map(mother => (
                    <option key={mother.id} value={mother.id}>{mother.name} ({mother.phone})</option>
                  ))}
                </select>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginBottom: '16px' }}>
                <div>
                  <label style={{ display: 'block', fontSize: '14px', fontWeight: '600', marginBottom: '6px', color: '#374151' }}>Systolic BP (mmHg)</label>
                  <input type="number" name="systolic_bp" placeholder="120" value={assessmentForm.systolic_bp} onChange={handleAssessmentChange} style={{ width: '100%', padding: '10px 12px', border: '1px solid #d1d5db', borderRadius: '6px', fontSize: '14px' }} />
                </div>
                <div>
                  <label style={{ display: 'block', fontSize: '14px', fontWeight: '600', marginBottom: '6px', color: '#374151' }}>Diastolic BP (mmHg)</label>
                  <input type="number" name="diastolic_bp" placeholder="80" value={assessmentForm.diastolic_bp} onChange={handleAssessmentChange} style={{ width: '100%', padding: '10px 12px', border: '1px solid #d1d5db', borderRadius: '6px', fontSize: '14px' }} />
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginBottom: '16px' }}>
                <div>
                  <label style={{ display: 'block', fontSize: '14px', fontWeight: '600', marginBottom: '6px', color: '#374151' }}>Heart Rate (bpm)</label>
                  <input type="number" name="heart_rate" placeholder="80" value={assessmentForm.heart_rate} onChange={handleAssessmentChange} style={{ width: '100%', padding: '10px 12px', border: '1px solid #d1d5db', borderRadius: '6px', fontSize: '14px' }} />
                </div>
                <div>
                  <label style={{ display: 'block', fontSize: '14px', fontWeight: '600', marginBottom: '6px', color: '#374151' }}>Blood Glucose (mg/dL)</label>
                  <input type="number" name="blood_glucose" placeholder="100" value={assessmentForm.blood_glucose} onChange={handleAssessmentChange} style={{ width: '100%', padding: '10px 12px', border: '1px solid #d1d5db', borderRadius: '6px', fontSize: '14px' }} />
                </div>
              </div>

              <div style={{ marginBottom: '16px' }}>
                <h4 style={{ color: '#1f2937', marginBottom: '12px', fontWeight: '600' }}>Clinical Symptoms (Optional)</h4>
                <div style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
                  gap: '12px',
                  background: '#f9fafb',
                  padding: '12px',
                  borderRadius: '6px'
                }}>
                  {[
                    { key: 'proteinuria', label: 'Proteinuria' },
                    { key: 'edema', label: 'Edema' },
                    { key: 'headache', label: 'Headache' },
                    { key: 'vision_changes', label: 'Vision Changes' },
                    { key: 'epigastric_pain', label: 'Epigastric Pain' },
                    { key: 'vaginal_bleeding', label: 'Vaginal Bleeding' }
                  ].map(symptom => (
                    <label key={symptom.key} style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer', fontSize: '14px' }}>
                      <input
                        type="checkbox"
                        checked={assessmentForm[symptom.key] === 1}
                        onChange={(e) => {
                          setAssessmentForm(prev => ({
                            ...prev,
                            [symptom.key]: e.target.checked ? 1 : 0
                          }))
                        }}
                        style={{ width: '18px', height: '18px', cursor: 'pointer' }}
                      />
                      <span>{symptom.label}</span>
                    </label>
                  ))}
                </div>
              </div>

              <button type="submit" disabled={loading} style={{ width: '100%', padding: '12px', background: '#667eea', color: 'white', border: 'none', borderRadius: '6px', fontWeight: '600', fontSize: '14px', cursor: loading ? 'not-allowed' : 'pointer', opacity: loading ? 0.6 : 1 }}>
                {loading ? 'Assessing...' : 'Assess Risk'}
              </button>
            </form>

            {riskResult && (
              <div style={{
                marginTop: '20px',
                padding: '16px',
                background: '#f0fdf4',
                border: '1px solid #86efac',
                borderRadius: '6px',
                color: '#166534'
              }}>
                <h3 style={{ margin: '0 0 12px 0' }}>✅ Risk Assessment Result</h3>
                <p><strong>Risk Score:</strong> {(riskResult.risk_score * 100).toFixed(1)}%</p>
                <p><strong>Risk Level:</strong> {riskResult.risk_level}</p>
                <p><strong>Risk Factors:</strong> {riskResult.risk_factors?.join(', ') || 'None'}</p>
              </div>
            )}
          </div>
        )}

        {/* All Mothers Tab */}
        {activeTab === 'all-mothers' && (
          <div style={{
            background: 'white',
            padding: '24px',
            borderRadius: '8px',
            boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
          }}>
            <h2 style={{ marginBottom: '16px', color: '#1f2937' }}>👥 All Registered Mothers - Complete Details</h2>
            {mothers.length === 0 ? (
              <p style={{ color: '#6b7280' }}>No mothers registered yet</p>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                {mothers.map(mother => {
                  const isExpanded = expandedMother === mother.id
                  const latestRisk = mother.latestRisk
                  const assessments = mother.assessments || []
                  
                  const getRiskColor = (level) => {
                    if (level === 'HIGH') return { bg: '#fee2e2', color: '#991b1b', border: '#fecaca', emoji: '🔴' }
                    if (level === 'MODERATE') return { bg: '#fef3c7', color: '#92400e', border: '#fcd34d', emoji: '🟡' }
                    return { bg: '#dcfce7', color: '#166534', border: '#bbf7d0', emoji: '🟢' }
                  }
                  
                  const riskStyle = latestRisk ? getRiskColor(latestRisk.risk_level) : null
                  
                  return (
                    <div
                      key={mother.id}
                      style={{
                        border: isExpanded ? '2px solid #667eea' : '1px solid #e5e7eb',
                        borderRadius: '8px',
                        overflow: 'hidden',
                        background: '#f9fafb',
                        transition: 'all 0.3s ease'
                      }}
                    >
                      <div
                        onClick={() => setExpandedMother(isExpanded ? null : mother.id)}
                        style={{
                          padding: '16px',
                          display: 'flex',
                          justifyContent: 'space-between',
                          alignItems: 'center',
                          cursor: 'pointer',
                          background: isExpanded ? '#f0f4f8' : '#f9fafb',
                          transition: 'all 0.2s ease'
                        }}
                      >
                        <div>
                          <h3 style={{ margin: '0 0 8px 0', color: '#1f2937', fontSize: '16px', fontWeight: '600' }}>
                            {mother.name}
                          </h3>
                          <p style={{ margin: '0', fontSize: '13px', color: '#6b7280' }}>
                            📱 {mother.phone} • 👤 Age: {mother.age} • 📍 {mother.location}
                          </p>
                        </div>
                        
                        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                          {latestRisk ? (
                            <div style={{
                              padding: '8px 16px',
                              borderRadius: '20px',
                              background: riskStyle.bg,
                              color: riskStyle.color,
                              fontWeight: '600',
                              fontSize: '13px',
                              border: `2px solid ${riskStyle.border}`,
                              textAlign: 'center'
                            }}>
                              {riskStyle.emoji} {latestRisk.risk_level}
                              <div style={{ fontSize: '11px', fontWeight: '500', marginTop: '2px' }}>
                                Score: {(latestRisk.risk_score * 100).toFixed(0)}%
                              </div>
                            </div>
                          ) : (
                            <div style={{
                              padding: '8px 16px',
                              borderRadius: '20px',
                              background: '#e5e7eb',
                              color: '#6b7280',
                              fontWeight: '600',
                              fontSize: '13px'
                            }}>
                              No Assessment
                            </div>
                          )}
                          
                          <div style={{
                            fontSize: '20px',
                            transition: 'transform 0.2s ease',
                            transform: isExpanded ? 'rotate(180deg)' : 'rotate(0deg)'
                          }}>
                            ▼
                          </div>
                        </div>
                      </div>

                      {isExpanded && (
                        <div style={{
                          padding: '16px',
                          borderTop: '1px solid #e5e7eb',
                          background: 'white'
                        }}>
                          <div style={{ marginBottom: '16px', paddingBottom: '16px', borderBottom: '1px solid #e5e7eb' }}>
                            <h4 style={{ margin: '0 0 12px 0', color: '#1f2937', fontSize: '14px', fontWeight: '600' }}>
                              📋 Complete Mother Details
                            </h4>
                            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '12px', fontSize: '13px' }}>
                              <div style={{ background: '#f3f4f6', padding: '10px', borderRadius: '6px' }}>
                                <div style={{ color: '#6b7280', fontWeight: '600', marginBottom: '4px' }}>Name</div>
                                <div style={{ color: '#1f2937' }}>{mother.name}</div>
                              </div>
                              <div style={{ background: '#f3f4f6', padding: '10px', borderRadius: '6px' }}>
                                <div style={{ color: '#6b7280', fontWeight: '600', marginBottom: '4px' }}>Phone</div>
                                <div style={{ color: '#1f2937' }}>{mother.phone}</div>
                              </div>
                              <div style={{ background: '#f3f4f6', padding: '10px', borderRadius: '6px' }}>
                                <div style={{ color: '#6b7280', fontWeight: '600', marginBottom: '4px' }}>Age</div>
                                <div style={{ color: '#1f2937' }}>{mother.age} years</div>
                              </div>
                              <div style={{ background: '#f3f4f6', padding: '10px', borderRadius: '6px' }}>
                                <div style={{ color: '#6b7280', fontWeight: '600', marginBottom: '4px' }}>BMI</div>
                                <div style={{ color: '#1f2937' }}>{mother.bmi}</div>
                              </div>
                              <div style={{ background: '#f3f4f6', padding: '10px', borderRadius: '6px' }}>
                                <div style={{ color: '#6b7280', fontWeight: '600', marginBottom: '4px' }}>Gravida</div>
                                <div style={{ color: '#1f2937' }}>{mother.gravida}</div>
                              </div>
                              <div style={{ background: '#f3f4f6', padding: '10px', borderRadius: '6px' }}>
                                <div style={{ color: '#6b7280', fontWeight: '600', marginBottom: '4px' }}>Parity</div>
                                <div style={{ color: '#1f2937' }}>{mother.parity}</div>
                              </div>
                              <div style={{ background: '#f3f4f6', padding: '10px', borderRadius: '6px' }}>
                                <div style={{ color: '#6b7280', fontWeight: '600', marginBottom: '4px' }}>Location</div>
                                <div style={{ color: '#1f2937' }}>{mother.location}</div>
                              </div>
                              <div style={{ background: '#f3f4f6', padding: '10px', borderRadius: '6px' }}>
                                <div style={{ color: '#6b7280', fontWeight: '600', marginBottom: '4px' }}>Language</div>
                                <div style={{ color: '#1f2937' }}>{mother.preferred_language === 'en' ? 'English' : mother.preferred_language === 'mr' ? 'Marathi' : 'Hindi'}</div>
                              </div>
                            </div>
                          </div>

                          <h4 style={{ margin: '0 0 12px 0', color: '#1f2937', fontSize: '14px', fontWeight: '600' }}>
                            📊 Assessment History ({assessments.length})
                          </h4>
                          
                          {assessments.length === 0 ? (
                            <p style={{ color: '#6b7280', margin: '0', fontSize: '14px' }}>No assessments recorded</p>
                          ) : (
                            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                              {assessments.map((assessment, idx) => {
                                const getRiskColorInner = (level) => {
                                  if (level === 'HIGH') return { bg: '#fee2e2', color: '#991b1b', border: '#fecaca', emoji: '🔴' }
                                  if (level === 'MODERATE') return { bg: '#fef3c7', color: '#92400e', border: '#fcd34d', emoji: '🟡' }
                                  return { bg: '#dcfce7', color: '#166534', border: '#bbf7d0', emoji: '🟢' }
                                }
                                const riskColorInner = getRiskColorInner(assessment.risk_level)
                                return (
                                  <div
                                    key={idx}
                                    style={{
                                      padding: '12px',
                                      background: riskColorInner.bg,
                                      border: `1px solid ${riskColorInner.border}`,
                                      borderRadius: '6px',
                                      display: 'flex',
                                      justifyContent: 'space-between',
                                      alignItems: 'flex-start'
                                    }}
                                  >
                                    <div style={{ flex: 1 }}>
                                      <div style={{ fontSize: '12px', color: riskColorInner.color, fontWeight: '600', marginBottom: '6px' }}>
                                        📅 {new Date(assessment.created_at).toLocaleDateString()} at {new Date(assessment.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                                      </div>
                                      <div style={{ fontSize: '13px', color: riskColorInner.color, lineHeight: '1.6' }}>
                                        <div><strong>BP:</strong> {assessment.systolic_bp}/{assessment.diastolic_bp} mmHg</div>
                                        <div><strong>HR:</strong> {assessment.heart_rate} bpm</div>
                                        <div><strong>Glucose:</strong> {assessment.blood_glucose} mg/dL</div>
                                        <div><strong>Hemoglobin:</strong> {assessment.hemoglobin} g/dL</div>
                                      </div>
                                    </div>
                                    
                                    <div style={{
                                      padding: '8px 12px',
                                      borderRadius: '16px',
                                      background: 'rgba(255,255,255,0.6)',
                                      color: riskColorInner.color,
                                      fontWeight: '600',
                                      fontSize: '12px',
                                      textAlign: 'center',
                                      marginLeft: '12px',
                                      whiteSpace: 'nowrap',
                                      border: `1px solid ${riskColorInner.border}`
                                    }}>
                                      {riskColorInner.emoji} {assessment.risk_level}
                                      <div style={{ fontSize: '11px', fontWeight: '500' }}>
                                        {(assessment.risk_score * 100).toFixed(0)}%
                                      </div>
                                    </div>
                                  </div>
                                )
                              })}
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  )
                })}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}