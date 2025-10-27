import React from 'react'
import { Heart } from 'lucide-react'

export default function Navbar() {
  return (
    <div className="bg-gradient-to-r from-blue-600 to-indigo-700 text-white shadow-xl">
      <div className="max-w-7xl mx-auto px-6 py-8">
        <div className="flex items-center justify-between flex-wrap gap-4">
          <div className="flex items-center gap-3">
            <Heart className="w-8 h-8 fill-current" />
            <div>
              <h1 className="text-3xl font-bold">MaatruRaksha AI</h1>
              <p className="text-blue-100 text-sm">Maternal Health Guardian System</p>
            </div>
          </div>
          <div className="text-right text-sm text-blue-100">
            <p className="font-medium">Telegram-Powered Care Coordination</p>
            <p className="mt-1">Maharashtra Maternal Health Initiative</p>
          </div>
        </div>
      </div>
    </div>
  )
}