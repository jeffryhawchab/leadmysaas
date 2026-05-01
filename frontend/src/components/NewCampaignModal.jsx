import { useState } from 'react'
import { X } from 'lucide-react'

export default function NewCampaignModal({ onClose, onCreated }) {
  const [form, setForm] = useState({ name: '', saas_description: '', target_audience: '' })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const submit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError('')
    try {
      const res = await fetch('/api/campaigns/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(form),
      })
      const data = await res.json()
      onCreated(data)
      onClose()
    } catch {
      setError('Something went wrong. Try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm px-4">
      <div className="bg-[#1a1a24] border border-white/10 rounded-2xl w-full max-w-lg shadow-2xl">
        <div className="flex items-center justify-between px-6 py-4 border-b border-white/10">
          <h2 className="text-lg font-semibold text-white">New Campaign</h2>
          <button onClick={onClose} className="text-slate-400 hover:text-white transition-colors cursor-pointer"><X size={18} /></button>
        </div>
        <form onSubmit={submit} className="px-6 py-5 space-y-4">
          {[
            { key: 'name', label: 'Campaign Name', placeholder: 'e.g. Q3 SaaS Outreach', type: 'input' },
            { key: 'saas_description', label: 'What does your SaaS do?', placeholder: 'e.g. A project management tool for remote engineering teams', type: 'textarea' },
            { key: 'target_audience', label: 'Target Audience', placeholder: 'e.g. CTOs at B2B SaaS startups with 10–200 employees', type: 'textarea' },
          ].map(field => (
            <div key={field.key}>
              <label className="block text-sm font-medium text-slate-300 mb-1.5">{field.label}</label>
              {field.type === 'input' ? (
                <input
                  required
                  value={form[field.key]}
                  onChange={e => setForm(p => ({ ...p, [field.key]: e.target.value }))}
                  placeholder={field.placeholder}
                  className="w-full bg-white/5 border border-white/10 focus:border-indigo-500 rounded-xl px-4 py-2.5 text-white placeholder-slate-500 outline-none transition-colors text-sm"
                />
              ) : (
                <textarea
                  required
                  rows={3}
                  value={form[field.key]}
                  onChange={e => setForm(p => ({ ...p, [field.key]: e.target.value }))}
                  placeholder={field.placeholder}
                  className="w-full bg-white/5 border border-white/10 focus:border-indigo-500 rounded-xl px-4 py-2.5 text-white placeholder-slate-500 outline-none transition-colors text-sm resize-none"
                />
              )}
            </div>
          ))}
          {error && <p className="text-red-400 text-sm">{error}</p>}
          <button
            type="submit"
            disabled={loading}
            className="w-full bg-indigo-600 hover:bg-indigo-500 disabled:opacity-60 text-white py-2.5 rounded-xl font-medium transition-all cursor-pointer"
          >
            {loading ? 'Creating...' : 'Create Campaign'}
          </button>
        </form>
      </div>
    </div>
  )
}
