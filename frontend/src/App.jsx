import { useState, useEffect } from 'react'
import Dashboard from './pages/Dashboard'
import CampaignDetail from './pages/CampaignDetail'
import './index.css'

export default function App() {
  const [page, setPage] = useState({ name: 'dashboard', params: {} })

  const navigate = (name, params = {}) => setPage({ name, params })

  return (
    <div className="min-h-screen">
      {page.name === 'dashboard' && <Dashboard navigate={navigate} />}
      {page.name === 'campaign' && <CampaignDetail id={page.params.id} navigate={navigate} />}
    </div>
  )
}
