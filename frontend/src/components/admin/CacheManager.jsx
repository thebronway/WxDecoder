import React, { useEffect, useState } from 'react';
import AdminLayout from './AdminLayout';
import api from '../../services/api';
import { Search, Trash2, Database, AlertTriangle } from 'lucide-react';

const CacheManager = () => {
  const [cache, setCache] = useState([]);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [tz, setTz] = useState("UTC");

  const [kiosks, setKiosks] = useState([]); // Add State

  const fetchData = async () => {
    setLoading(true);
    try {
      const [cacheData, settingsData, kioskData] = await Promise.all([
          api.get("/api/admin/cache"),
          api.get("/api/admin/settings"),
          api.get("/api/kiosk/list")
      ]);
      setCache(cacheData);
      setKiosks(kioskData); // Set Kiosks
      if (Array.isArray(settingsData.config)) {
           const foundTz = settingsData.config.find(c => c.key === "app_timezone");
           if (foundTz) setTz(foundTz.value);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchData(); }, []);

  const formatTime = (isoString) => {
    if (!isoString) return "-";
    return new Date(isoString).toLocaleTimeString('en-US', { timeZone: tz, hour: '2-digit', minute: '2-digit' });
  };

  const handleClear = async (key = null) => {
    const msg = key ? `Clear cache for ${key}?` : "FLUSH ALL CACHED REPORTS? This cannot be undone.";
    if (!confirm(msg)) return;

    try {
      await api.post("/api/admin/cache/clear", { key });
      fetchData();
    } catch (err) {
      alert("Clear failed");
    }
  };

  const filtered = cache.filter(item => 
      item.icao.toLowerCase().includes(search.toLowerCase()) || 
      item.category.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <AdminLayout>
      <div className="flex flex-col md:flex-row justify-between items-center mb-6 gap-4">
        <div>
            <h1 className="text-2xl font-bold text-white tracking-tight">Cache Manager</h1>
            <p className="text-neutral-500 text-sm">Stored Weather & AI Analyses</p>
        </div>
        
        <div className="flex items-center gap-3 w-full md:w-auto">
            <div className="relative flex-1 md:w-64">
                <Search className="absolute left-3 top-2.5 text-neutral-500 w-4 h-4" />
                <input 
                    type="text" 
                    placeholder="Search ICAO..." 
                    className="w-full bg-neutral-900 border border-neutral-700 rounded-full pl-10 pr-4 py-2 text-sm text-white focus:outline-none focus:border-blue-500"
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                />
            </div>
            <button 
                onClick={() => handleClear()}
                className="bg-red-600/20 hover:bg-red-600 text-red-500 hover:text-white border border-red-600/50 px-4 py-2 rounded-full text-xs font-bold transition-all flex items-center gap-2 whitespace-nowrap"
            >
                <AlertTriangle size={14} /> FLUSH ALL
            </button>
        </div>
      </div>

      <div className="border border-neutral-800 rounded bg-neutral-900/20 overflow-hidden shadow-2xl">
        <table className="w-full text-left text-xs">
            <thead className="bg-neutral-800 text-neutral-400 uppercase tracking-wider">
                <tr>
                    <th className="p-4">Airport</th>
                    <th className="p-4">Wx Source</th>
                    <th className="p-4">Profile</th>
                    <th className="p-4">Active Kiosks</th>
                    <th className="p-4">Stored At</th>
                    <th className="p-4">Expires At ({tz})</th>
                    <th className="p-4 text-right">Action</th>
                </tr>
            </thead>
            <tbody className="divide-y divide-neutral-800 text-gray-300 font-mono">
                {loading ? (
                    <tr><td colSpan="5" className="p-8 text-center text-blue-500 animate-pulse">LOADING CACHED DATA...</td></tr>
                ) : filtered.length === 0 ? (
                    <tr><td colSpan="5" className="p-8 text-center text-neutral-500">Cache is empty.</td></tr>
                ) : filtered.map((row) => {
                    // Match Kiosks to this Cache Row
                    const matchingKiosks = kiosks.filter(k => 
                        k.target_icao === row.icao && 
                        (
                            // 1. Kiosk has explicit override matching this row's source
                            (k.weather_override_icao && k.weather_override_icao === row.weather_source) || 
                            // 2. Kiosk is Auto (No override) - It matches any entry for this target
                            (!k.weather_override_icao)
                        )
                    );

                    return (
                    <tr key={row.key} className="hover:bg-neutral-800/50 group">
                        <td className="p-4 text-white font-bold">{row.icao}</td>
                        
                        {/* WX SOURCE COLUMN */}
                        <td className="p-4 font-mono text-yellow-500">
                            {row.weather_source || "-"}
                        </td>

                        <td className="p-4">
                            <span className={`px-2 py-0.5 rounded text-[10px] border ${
                                row.category === 'SMALL' ? 'border-green-900 text-green-400' : 
                                row.category === 'MEDIUM' ? 'border-blue-900 text-blue-400' : 'border-purple-900 text-purple-400'
                            }`}>
                                {row.category}
                            </span>
                        </td>

                        {/* KIOSK COLUMN */}
                        <td className="p-4">
                            <div className="flex flex-wrap gap-1">
                                {matchingKiosks.length > 0 ? matchingKiosks.map(k => (
                                    <span key={k.slug} className="px-2 py-0.5 bg-neutral-700 rounded text-[10px] text-white" title={k.subscriber_name}>
                                        {k.slug}
                                    </span>
                                )) : <span className="text-neutral-600">-</span>}
                            </div>
                        </td>

                        <td className="p-4 text-neutral-500">{formatTime(row.timestamp)}</td>
                        <td className="p-4 text-yellow-500/80">{formatTime(row.expires_at)}</td>
                        <td className="p-4 text-right">
                            <button 
                                onClick={() => handleClear(row.key)}
                                className="text-neutral-600 hover:text-red-500 transition-colors p-2"
                                title="Delete this entry"
                            >
                                <Trash2 size={16} />
                            </button>
                        </td>
                    </tr>
                );})}
            </tbody>
        </table>
      </div>
    </AdminLayout>
  );
};

export default CacheManager;