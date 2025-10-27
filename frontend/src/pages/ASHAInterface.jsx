import React, { useState } from 'react'
import { CheckCircle, AlertCircle } from 'lucide-react'

export default function ASHAInterface() {
  const [tasks, setTasks] = useState([
    {
      id: 1,
      mother: 'Priya Sharma',
      priority: 'High',
      task: 'Collect vital signs and conduct health check',
      status: 'pending'
    },
    {
      id: 2,
      mother: 'Anjali Desai',
      priority: 'Medium',
      task: 'Follow-up on medication adherence',
      status: 'pending'
    }
  ])

  const handleTaskComplete = (id) => {
    setTasks(tasks.map(task =>
      task.id === id ? { ...task, status: 'completed' } : task
    ))
  }

  const getPriorityColor = (priority) => {
    if (priority === 'High') return 'bg-red-100 text-red-800'
    if (priority === 'Medium') return 'bg-yellow-100 text-yellow-800'
    return 'bg-green-100 text-green-800'
  }

  return (
    <div className="max-w-4xl mx-auto px-6 py-8">
      <h1 className="text-3xl font-bold mb-6">ASHA Worker Dashboard</h1>

      <div className="bg-blue-50 border border-blue-200 p-4 rounded-lg mb-6">
        <p className="text-blue-900">
          📋 You have <strong>{tasks.length}</strong> mothers to visit today.
          Complete tasks to update records and earn performance incentives.
        </p>
      </div>

      <div className="space-y-4">
        {tasks.map(task => (
          <div key={task.id} className="bg-white p-6 rounded-lg shadow-md hover:shadow-lg transition">
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <h3 className="text-lg font-bold">{task.mother}</h3>
                <p className="text-gray-600 mt-2">{task.task}</p>
                <div className="flex items-center gap-4 mt-4">
                  <span className={`px-3 py-1 rounded-full text-sm font-semibold ${getPriorityColor(task.priority)}`}>
                    {task.priority}
                  </span>
                  <span className={`text-sm ${task.status === 'completed' ? 'text-green-600' : 'text-yellow-600'}`}>
                    {task.status === 'completed' ? '✓ Completed' : '⏳ Pending'}
                  </span>
                </div>
              </div>
              {task.status !== 'completed' && (
                <button
                  onClick={() => handleTaskComplete(task.id)}
                  className="bg-indigo-600 text-white px-4 py-2 rounded-lg hover:bg-indigo-700 transition"
                >
                  Mark Complete
                </button>
              )}
              {task.status === 'completed' && (
                <CheckCircle className="w-6 h-6 text-green-600" />
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}