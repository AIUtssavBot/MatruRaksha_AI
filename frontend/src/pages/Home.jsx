import React from 'react'
import { Heart, Shield, Users, Zap } from 'lucide-react'
import { FEATURES } from '../utils/constants'

export default function Home() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      {/* Hero Section */}
      <div className="bg-gradient-to-r from-blue-600 to-indigo-700 text-white py-16 px-6">
        <div className="max-w-4xl mx-auto text-center">
          <Heart className="w-16 h-16 mx-auto mb-4 fill-current" />
          <h1 className="text-4xl font-bold mb-4">MaatruRaksha AI</h1>
          <p className="text-xl text-blue-100 mb-8">
            Maternal Health Guardian - AI-Powered Risk Prediction & Care Coordination
          </p>
          <a
            href="/#dashboard"
            className="inline-block bg-white text-indigo-700 px-8 py-3 rounded-lg font-bold hover:bg-blue-50 transition"
          >
            Get Started
          </a>
        </div>
      </div>

      {/* Features Section */}
      <div className="max-w-6xl mx-auto px-6 py-16">
        <h2 className="text-3xl font-bold text-center mb-12">Key Features</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {[
            { icon: Shield, title: 'Risk Prediction', desc: 'Real-time ML-based pregnancy risk detection' },
            { icon: Zap, title: 'Instant Alerts', desc: 'Telegram notifications for critical events' },
            { icon: Users, title: 'Care Coordination', desc: 'Automated appointment scheduling & referrals' },
            { icon: Heart, title: '24/7 Support', desc: 'Emergency response system always active' }
          ].map((feature, idx) => {
            const Icon = feature.icon
            return (
              <div key={idx} className="bg-white p-6 rounded-lg shadow-md hover:shadow-lg transition">
                <Icon className="w-12 h-12 text-indigo-600 mb-4" />
                <h3 className="text-lg font-bold mb-2">{feature.title}</h3>
                <p className="text-gray-600 text-sm">{feature.desc}</p>
              </div>
            )
          })}
        </div>
      </div>

      {/* Impact Section */}
      <div className="bg-gradient-to-r from-indigo-500 to-blue-600 text-white py-12 px-6 my-16">
        <div className="max-w-4xl mx-auto">
          <h2 className="text-3xl font-bold text-center mb-12">Expected Impact</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {[
              { number: '40%', label: 'MMR Reduction', desc: 'Preventable maternal deaths avoided' },
              { number: '5000+', label: 'Lives Saved', desc: 'Annually through early detection' },
              { number: '90%', label: 'ANC Compliance', desc: 'Antenatal care attendance rate' }
            ].map((impact, idx) => (
              <div key={idx} className="text-center">
                <p className="text-4xl font-bold mb-2">{impact.number}</p>
                <p className="text-lg font-semibold mb-1">{impact.label}</p>
                <p className="text-blue-100 text-sm">{impact.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* CTA Section */}
      <div className="max-w-4xl mx-auto px-6 py-16 text-center">
        <h2 className="text-2xl font-bold mb-4">Ready to Save Lives?</h2>
        <p className="text-gray-600 mb-8">
          MaatruRaksha AI combines artificial intelligence with maternal health expertise to provide
          predictive risk assessment, automated care coordination, and 24/7 emergency support.
        </p>
        <a
          href="/#dashboard"
          className="inline-block bg-indigo-600 text-white px-8 py-3 rounded-lg font-bold hover:bg-indigo-700 transition"
        >
          Access Dashboard
        </a>
      </div>
    </div>
  )
}