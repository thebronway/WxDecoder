import React, { useEffect, useState } from 'react';
import AdminLayout from './AdminLayout';
import api from '../../services/api';
import { Monitor, Trash2, Plus } from 'lucide-react';

const KioskManager = () => {
  const [kiosks, setKiosks] = useState([]);
  const [form, setForm] = useState({ icao: '', subscriber_name: '', default_profile: 'small' });
  const [loading, setLoading] = useState(true);

  const fetchKiosks = async () => {
    try {
      const res = await api.get("/api/admin/list"); // This endpoint needs to map to kiosk.list, wait, checking router... 
      // Correction: The backend defines @router.get("/list") inside kiosk.py mounted at /api/kiosk
      // But it is protected by Admin Key. Let's ensure the path matches: /api/kiosk/list
      const resCorrected = await api.get("/api/kiosk/list");
      setKiosks(resCorrected);
    } catch (e) { console.error(e); } 
    finally { setLoading(false); }
  };

  useEffect(() => { fetchKiosks(); }, []);

  const handleAdd = async (e) => {
    e.preventDefault();
    try {
        await api.post("/api/kiosk/add", {
            ...form,
            allowed_profiles: ["small", "medium", "large"] // Defaulting to all for now
        });
        setForm({ icao: '', subscriber_name: '', default_profile: 'small' });
        fetchKiosks();
    } catch (e) { alert("Failed to add kiosk"); }
  };

  const handleRemove = async (icao) => {
      if(!confirm("Remove Kiosk?")) return;
      await api.delete(`/api/kiosk/remove/${icao}`);
      fetchKiosks();
  };

  return (
    <AdminLayout>
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-white">Kiosk Management</h1>
        <p className="text-neutral-500 text-sm">Manage authorized airports for Kiosk Mode (TV Display).</p>
      </div>

      {/* ADD FORM */}
      <div className="bg-neutral-900 border border-neutral-800 p-6 rounded-xl mb-8">
          <h3 className="text-blue-400 font-bold uppercase tracking-widest text-xs mb-4">Authorize New Kiosk</h3>
          <form onSubmit={handleAdd} className="flex flex-col md:flex-row gap-4 items-end">
              <div className="flex-1 w-full">
                  <label className="block text-xs font-bold text-neutral-500 mb-1">Airport ICAO</label>
                  <input required className="w-full bg-black border border-neutral-700 rounded p-2 text-white font-mono uppercase" placeholder="KBOS" value={form.icao} onChange={e => setForm({...form, icao: e.target.value.toUpperCase()})} />
              </div>
              <div className="flex-[2] w-full">
                  <label className="block text-xs font-bold text-neutral-500 mb-1">Subscriber / School Name</label>
                  <input required className="w-full bg-black border border-neutral-700 rounded p-2 text-white" placeholder="Boston Flight Academy" value={form.subscriber_name} onChange={e => setForm({...form, subscriber_name: e.target.value})} />
              </div>
              <div className="flex-1 w-full">
                  <label className="block text-xs font-bold text-neutral-500 mb-1">Default Profile</label>
                  <select className="w-full bg-black border border-neutral-700 rounded p-2 text-white" value={form.default_profile} onChange={e => setForm({...form, default_profile: e.target.value})}>
                      <option value="small">Small</option>
                      <option value="medium">Medium</option>
                      <option value="large">Large</option>
                  </select>
              </div>
              <button type="submit" className="bg-blue-600 hover:bg-blue-500 text-white font-bold py-2 px-6 rounded flex items-center gap-2">
                  <Plus size={16} /> Add
              </button>
          </form>
      </div>

      {/* LIST */}
      <div className="bg-neutral-900/50 border border-neutral-800 rounded-xl overflow-hidden">
        <table className="w-full text-left text-sm text-gray-400">
            <thead className="bg-neutral-800 text-neutral-500 font-bold uppercase text-xs">
                <tr>
                    <th className="p-4">ICAO</th>
                    <th className="p-4">Subscriber</th>
                    <th className="p-4">Default Profile</th>
                    <th className="p-4 text-right">Actions</th>
                </tr>
            </thead>
            <tbody className="divide-y divide-neutral-800">
                {kiosks.map(k => (
                    <tr key={k.icao} className="hover:bg-neutral-800/50">
                        <td className="p-4 font-bold text-white font-mono flex items-center gap-2">
                            <Monitor size={14} className="text-green-500" /> {k.icao}
                        </td>
                        <td className="p-4">{k.subscriber_name}</td>
                        <td className="p-4 uppercase text-xs font-bold tracking-wider">{k.default_profile}</td>
                        <td className="p-4 text-right">
                            <button onClick={() => handleRemove(k.icao)} className="text-red-500 hover:text-white transition-colors">
                                <Trash2 size={16} />
                            </button>
                        </td>
                    </tr>
                ))}
                {kiosks.length === 0 && !loading && <tr><td colSpan={4} className="p-8 text-center italic">No active kiosks.</td></tr>}
            </tbody>
        </table>
      </div>
    </AdminLayout>
  );
};

export default KioskManager;