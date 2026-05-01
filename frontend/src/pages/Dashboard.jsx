import { useState, useEffect } from 'react'
import { Plus, Zap, Users, TrendingUp } from 'lucide-react'
import NewCampaignModal from '../components/NewCampaignModal'

export default function Dashboard({ navigate }) {
  const [campaigns, setCampaigns] = useState([])
  const [loading, setLoading] = useState(true)
  const [showModal, setShowModal] = useState(false)

  const fetchCampaigns = () => {
    fetch('/api/campaigns/')
      .then(r => r.json())
      .then(data => { setCampaigns(data); setLoading(false) })
  }

  useEffect(() => { fetchCampaigns() }, [])

  const totalLeads = campaigns.reduce((s, c) => s + c.lead_count, 0)
  const avgScore = campaigns.length
    ? Math.round(campaigns.flatMap(c => c.leads).reduce((s, l) => s + l.ai_score, 0) / (totalLeads || 1))
    : 0

  return (
    <div className="max-w-6xl mx-auto px-6 py-10">
      {/* Header */}
      <div className="flex items-center justify-between mb-10">
        <div>
          <h1 className="text-3xl font-bold text-white tracking-tight">🚀 LeadMySaaS</h1>
          <p className="text-slate-400 mt-1 text-sm">AI-powered B2B lead generation</p>
        </div>
        <button
          onClick={() => setShowModal(true)}
          className="flex items-center gap-2 bg-indigo-600 hover:bg-indigo-500 text-white px-4 py-2.5 rounded-xl font-medium transition-all duration-150 shadow-lg shadow-indigo-900/40 cursor-pointer"
        >
          <Plus size={16} /> New Campaign
        </button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-3 gap-4 mb-10">
        {[
          { label: 'Campaigns', value: campaigns.length, icon: <Zap size={18} />, color: 'text-indigo-400' },
          { label: 'Total Leads', value: totalLeads, icon: <Users size={18} />, color: 'text-emerald-400' },
          { label: 'Avg AI Score', value: `${avgScore}/100`, icon: <TrendingUp size={18} />, color: 'text-amber-400' },
        ].map(stat => (
          <div key={stat.label} className="bg-white/5 border border-white/10 rounded-2xl p-5">
            <div className={`${stat.color} mb-2`}>{stat.icon}</div>
            <div className="text-2xl font-bold text-white">{stat.value}</div>
            <div className="text-slate-400 text-sm">{stat.label}</div>
          </div>
        ))}
      </div>

      {/* Campaign grid */}
      {loading ? (
        <div className="text-center py-20 text-slate-500">Loading...</div>
      ) : campaigns.length === 0 ? (
        <div className="text-center py-24 border border-dashed border-white/10 rounded-2xl">
          <p className="text-slate-400 text-lg mb-4">No campaigns yet</p>
          <button
            onClick={() => setShowModal(true)}
            className="bg-indigo-600 hover:bg-indigo-500 text-white px-5 py-2.5 rounded-xl font-medium transition-all cursor-pointer"
          >
            Create your first campaign
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {campaigns.map(c => (
            <CampaignCard key={c.id} campaign={c} onClick={() => navigate('campaign', { id: c.id })} />
          ))}
        </div>
      )}

      {showModal && (
        <NewCampaignModal
          onClose={() => setShowModal(false)}
          onCreated={(c) => { fetchCampaigns(); navigate('campaign', { id: c.id }) }}
        />
      )}
    </div>
  )
}

function CampaignCard({ campaign, onClick }) {
  const qualified = campaign.leads.filter(l => l.status === 'qualified').length
  const withEmail = campaign.leads.filter(l => l.email).length

  return (
    <div
      onClick={onClick}
      className="bg-white/5 border border-white/10 hover:border-indigo-500/50 hover:bg-white/8 rounded-2xl p-5 cursor-pointer transition-all duration-200 group"
    >
      <div className="flex items-start justify-between mb-3">
        <h3 className="font-semibold text-white group-hover:text-indigo-300 transition-colors">{campaign.name}</h3>
        <span className="text-xs text-slate-500 shrink-0 ml-2">
          {new Date(campaign.created_at).toLocaleDateString()}
        </span>
      </div>
      <p className="text-slate-400 text-sm line-clamp-2 mb-4">{campaign.target_audience}</p>
      <div className="flex gap-3 text-xs">
        <span className="bg-indigo-500/15 text-indigo-300 px-2.5 py-1 rounded-full">{campaign.lead_count} leads</span>
        <span className="bg-emerald-500/15 text-emerald-300 px-2.5 py-1 rounded-full">{qualified} qualified</span>
        <span className="bg-amber-500/15 text-amber-300 px-2.5 py-1 rounded-full">{withEmail} emails</span>
      </div>
    </div>
  )
}
