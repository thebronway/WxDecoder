import React, { useEffect, useState } from 'react';
import AdminLayout from './AdminLayout';
import api from '../../services/api';
import { Monitor, Trash2, Plus, Globe, Link as LinkIcon } from 'lucide-react';

const KioskManager = () => {
  const [kiosks, setKiosks] = useState([]);
  const [form, setForm] = useState({ 
      slug: '', 
      target_icao: '', 
      subscriber_name: '', 
      default_profile: 'small',
      weather_override_icao: '',
      title_override: ''
  });
  const [loading, setLoading] = useState(true);

  const fetchKiosks = async () => {
    try {
      const res = await api.get("/api/kiosk/list");
      setKiosks(res);
    } catch (e) { console.error(e); } 
    finally { setLoading(false); }
  };

  useEffect(() => { fetchKiosks(); }, []);

  const handleAdd = async (e) => {
    e.preventDefault();
    try {
        await api.post("/api/kiosk/add", form);
        setForm({ 
            slug: '', target_icao: '', subscriber_name: '', default_profile: 'small',
            weather_override_icao: '', title_override: ''
        });
        fetchKiosks();
    } catch (e) { alert("Failed to add kiosk"); }
  };

  const handleRemove = async (slug) => {
      if(!confirm("Delete Kiosk Profile?")) return;
      await api.delete(`/api/kiosk/remove/${slug}`);
      fetchKiosks();
  };

  return (
    <AdminLayout>
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-white">Kiosk Profiles</h1>
        <p className="text-neutral-500 text-sm">Manage client-specific kiosk URLs and configurations.</p>
      </div>

      {/* ADD FORM */}
      <div className="bg-neutral-900 border border-neutral-800 p-6 rounded-xl mb-8">
          <h3 className="text-blue-400 font-bold uppercase tracking-widest text-xs mb-4">Create New Profile</h3>
          <form onSubmit={handleAdd} className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                      <label className="block text-xs font-bold text-neutral-500 mb-1">Subscriber Name</label>
                      <input required className="w-full bg-black border border-neutral-700 rounded p-2 text-white" placeholder="Bob's Flight School" value={form.subscriber_name} onChange={e => setForm({...form, subscriber_name: e.target.value})} />
                  </div>
                  <div>
                      <label className="block text-xs font-bold text-neutral-500 mb-1">URL Slug (ID)</label>
                      <input required className="w-full bg-black border border-neutral-700 rounded p-2 text-white font-mono" placeholder="bobs-flight-school" value={form.slug} onChange={e => setForm({...form, slug: e.target.value.toLowerCase().replace(/\s+/g, '-')})} />
                  </div>
              </div>
              
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                  <div className="md:col-span-1">
                      <label className="block text-xs font-bold text-neutral-500 mb-1">Target ICAO</label>
                      <input required className="w-full bg-black border border-neutral-700 rounded p-2 text-white font-mono uppercase" placeholder="K123" value={form.target_icao} onChange={e => setForm({...form, target_icao: e.target.value.toUpperCase()})} />
                  </div>
                  <div className="md:col-span-1">
                      <label className="block text-xs font-bold text-neutral-500 mb-1">Weather Override (Opt)</label>
                      <input className="w-full bg-black border border-neutral-700 rounded p-2 text-white font-mono uppercase" placeholder="KBOS" value={form.weather_override_icao} onChange={e => setForm({...form, weather_override_icao: e.target.value.toUpperCase()})} />
                  </div>
                  <div className="md:col-span-1">
                      <label className="block text-xs font-bold text-neutral-500 mb-1">Default Profile</label>
                      <select className="w-full bg-black border border-neutral-700 rounded p-2 text-white" value={form.default_profile} onChange={e => setForm({...form, default_profile: e.target.value})}>
                          <option value="small">Small</option>
                          <option value="medium">Medium</option>
                          <option value="large">Large</option>
                      </select>
                  </div>
                  <div className="md:col-span-1">
                      <label className="block text-xs font-bold text-neutral-500 mb-1">Title Override (Opt)</label>
                      <input className="w-full bg-black border border-neutral-700 rounded p-2 text-white" placeholder="Custom Page Title" value={form.title_override} onChange={e => setForm({...form, title_override: e.target.value})} />
                  </div>
              </div>

              <div className="pt-2">
                <button type="submit" className="bg-blue-600 hover:bg-blue-500 text-white font-bold py-2 px-6 rounded flex items-center gap-2">
                    <Plus size={16} /> Create Profile
                </button>
              </div>
          </form>
      </div>

      {/* LIST */}
      <div className="bg-neutral-900/50 border border-neutral-800 rounded-xl overflow-hidden">
        <table className="w-full text-left text-sm text-gray-400">
            <thead className="bg-neutral-800 text-neutral-500 font-bold uppercase text-xs">
                <tr>
                    <th className="p-4">Client / Slug</th>
                    <th className="p-4">Configuration</th>
                    <th className="p-4">Link</th>
                    <th className="p-4 text-right">Actions</th>
                </tr>
            </thead>
            <tbody className="divide-y divide-neutral-800">
                {kiosks.map(k => (
                    <tr key={k.slug} className="hover:bg-neutral-800/50">
                        <td className="p-4">
                            <div className="font-bold text-white">{k.subscriber_name}</div>
                            <div className="text-xs font-mono text-neutral-500">{k.slug}</div>
                        </td>
                        <td className="p-4">
                            <div className="flex items-center gap-2 mb-1">
                                <span className="text-xs font-bold bg-neutral-800 px-1.5 py-0.5 rounded border border-neutral-700 text-green-400">TGT: {k.target_icao}</span>
                                {k.weather_override_icao && (
                                    <span className="text-xs font-bold bg-neutral-800 px-1.5 py-0.5 rounded border border-neutral-700 text-yellow-400">WX: {k.weather_override_icao}</span>
                                )}
                            </div>
                            <div className="text-xs text-neutral-500">{k.title_override || "(Default Title)"} • {k.default_profile.toUpperCase()}</div>
                        </td>
                        <td className="p-4">
                            <a href={`/kiosk/${k.slug}`} target="_blank" rel="noreferrer" className="text-blue-500 hover:text-white flex items-center gap-1 text-xs font-bold uppercase tracking-wider">
                                <LinkIcon size={12} /> Open Kiosk
                            </a>
                        </td>
                        <td className="p-4 text-right">
                            <button onClick={() => handleRemove(k.slug)} className="text-red-500 hover:text-white transition-colors">
                                <Trash2 size={16} />
                            </button>
                        </td>
                    </tr>
                ))}
                {kiosks.length === 0 && !loading && <tr><td colSpan={4} className="p-8 text-center italic">No profiles found.</td></tr>}
            </tbody>
        </table>
      </div>
    </AdminLayout>
  );
};

export default KioskManager;