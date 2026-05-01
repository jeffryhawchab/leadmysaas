import { useState, useEffect } from 'react'
import { ArrowLeft, Zap, ExternalLink, Mail, Building2, Briefcase, Download } from 'lucide-react'

const STATUS_OPTIONS = ['new', 'contacted', 'qualified', 'rejected']
const STATUS_STYLES = {
  new: 'bg-slate-500/20 text-slate-300 border-slate-500/30',
  contacted: 'bg-blue-500/20 text-blue-300 border-blue-500/30',
  qualified: 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30',
  rejected: 'bg-red-500/20 text-red-300 border-red-500/30',
}

export default function CampaignDetail({ id, navigate }) {
  const [campaign, setCampaign] = useState(null)
  const [scraping, setScraping] = useState(false)
  const [filter, setFilter] = useState('all')
  const [toast, setToast] = useState(null)

  const showToast = (msg, type = 'success') => {
    setToast({ msg, type })
    setTimeout(() => setToast(null), 3500)
  }

  const fetchCampaign = () =>
    fetch(`/api/campaigns/${id}/`).then(r => r.json()).then(setCampaign)

  useEffect(() => { fetchCampaign() }, [id])

  const runScrape = async () => {
    setScraping(true)
    try {
      const res = await fetch(`/api/campaigns/${id}/scrape/`, { method: 'POST' })
      const data = await res.json()
      if (data.error) throw new Error(data.error)
      setCampaign(data.campaign)
      showToast(`✅ Found ${data.created} new, ${data.updated} updated!`)
    } catch (e) {
      showToast(`❌ ${e.message}`, 'error')
    } finally {
      setScraping(false)
    }
  }

  const updateStatus = async (leadId, status) => {
    await fetch(`/api/leads/${leadId}/`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status }),
    })
    setCampaign(prev => ({
      ...prev,
      leads: prev.leads.map(l => l.id === leadId ? { ...l, status } : l),
    }))
  }

  if (!campaign) return <div className="text-center py-20 text-slate-500">Loading...</div>

  const leads = filter === 'all' ? campaign.leads : campaign.leads.filter(l => l.status === filter)

  return (
    <div className="max-w-6xl mx-auto px-6 py-10">
      {/* Toast */}
      {toast && (
        <div className={`fixed top-5 right-5 z-50 px-5 py-3 rounded-xl shadow-xl text-sm font-medium transition-all
          ${toast.type === 'error' ? 'bg-red-900/80 text-red-200 border border-red-700' : 'bg-emerald-900/80 text-emerald-200 border border-emerald-700'}`}>
          {toast.msg}
        </div>
      )}

      {/* Header */}
      <div className="flex items-start justify-between mb-8">
        <div className="flex items-start gap-4">
          <button onClick={() => navigate('dashboard')} className="mt-1 text-slate-400 hover:text-white transition-colors cursor-pointer">
            <ArrowLeft size={20} />
          </button>
          <div>
            <h1 className="text-2xl font-bold text-white">{campaign.name}</h1>
            <p className="text-slate-400 text-sm mt-1 max-w-xl">{campaign.target_audience}</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <a
            href={`/api/campaigns/${id}/export/`}
            className="flex items-center gap-2 bg-white/5 hover:bg-white/10 border border-white/10 text-slate-300 px-4 py-2.5 rounded-xl font-medium transition-all cursor-pointer"
          >
            <Download size={15} /> Export Excel
          </a>
          <button
            onClick={runScrape}
            disabled={scraping}
            className="flex items-center gap-2 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-60 disabled:cursor-not-allowed text-white px-4 py-2.5 rounded-xl font-medium transition-all shadow-lg shadow-indigo-900/40 cursor-pointer"
          >
            <Zap size={15} className={scraping ? 'animate-pulse' : ''} />
            {scraping ? 'Scraping...' : 'Run AI Scrape'}
          </button>
        </div>
      </div>

      {/* AI Queries */}
      {campaign.ai_search_queries && (
        <div className="bg-white/5 border border-white/10 rounded-2xl p-4 mb-6">
          <p className="text-xs text-slate-400 font-medium uppercase tracking-wider mb-2">AI-Generated Queries</p>
          <div className="flex flex-wrap gap-2">
            {campaign.ai_search_queries.split('\n').filter(Boolean).map((q, i) => (
              <span key={i} className="text-xs bg-indigo-500/10 text-indigo-300 border border-indigo-500/20 px-3 py-1 rounded-full">{q}</span>
            ))}
          </div>
        </div>
      )}

      {/* Filter tabs */}
      <div className="flex gap-2 mb-6">
        {['all', ...STATUS_OPTIONS].map(s => (
          <button
            key={s}
            onClick={() => setFilter(s)}
            className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-all cursor-pointer capitalize
              ${filter === s ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-white hover:bg-white/5'}`}
          >
            {s} {s === 'all' ? `(${campaign.leads.length})` : `(${campaign.leads.filter(l => l.status === s).length})`}
          </button>
        ))}
      </div>

      {/* Leads */}
      {leads.length === 0 ? (
        <div className="text-center py-16 border border-dashed border-white/10 rounded-2xl text-slate-500">
          {campaign.leads.length === 0 ? 'No leads yet — run AI Scrape to find leads.' : 'No leads match this filter.'}
        </div>
      ) : (
        <div className="grid gap-3">
          {leads.map(lead => (
            <LeadCard key={lead.id} lead={lead} onStatusChange={updateStatus} />
          ))}
        </div>
      )}
    </div>
  )
}

function LeadCard({ lead, onStatusChange }) {
  const scoreColor = lead.ai_score >= 70 ? 'text-emerald-400' : lead.ai_score >= 40 ? 'text-amber-400' : 'text-slate-400'
  const scoreBg = lead.ai_score >= 70 ? 'bg-emerald-500/10' : lead.ai_score >= 40 ? 'bg-amber-500/10' : 'bg-slate-500/10'

  return (
    <div className="bg-white/5 border border-white/10 hover:border-white/20 rounded-2xl p-4 flex items-center gap-4 transition-all">
      {/* Score */}
      <div className={`${scoreBg} ${scoreColor} rounded-xl w-14 h-14 flex flex-col items-center justify-center shrink-0`}>
        <span className="text-lg font-bold leading-none">{lead.ai_score}</span>
        <span className="text-[10px] opacity-60">score</span>
      </div>

      {/* Info */}
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 mb-1">
          <span className="font-semibold text-white truncate">{lead.name || 'Unknown'}</span>
          {lead.linkedin_url && (
            <a href={lead.linkedin_url} target="_blank" rel="noreferrer" className="text-slate-500 hover:text-indigo-400 transition-colors shrink-0">
              <ExternalLink size={13} />
            </a>
          )}
        </div>
        <div className="flex flex-wrap gap-x-4 gap-y-1 text-xs text-slate-400">
          {lead.title && <span className="flex items-center gap-1"><Briefcase size={11} />{lead.title}</span>}
          {lead.company && <span className="flex items-center gap-1"><Building2 size={11} />{lead.company}</span>}
          {lead.email && (
            <a href={`mailto:${lead.email}`} className="flex items-center gap-1 text-indigo-400 hover:text-indigo-300 transition-colors">
              <Mail size={11} />{lead.email}
            </a>
          )}
        </div>
      </div>

      {/* Status */}
      <select
        value={lead.status}
        onChange={e => onStatusChange(lead.id, e.target.value)}
        className={`text-xs border rounded-lg px-2.5 py-1.5 bg-transparent font-medium cursor-pointer outline-none transition-all ${STATUS_STYLES[lead.status]}`}
      >
        {STATUS_OPTIONS.map(s => (
          <option key={s} value={s} className="bg-slate-900 text-white capitalize">{s}</option>
        ))}
      </select>
    </div>
  )
}
