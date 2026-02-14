import React, { useEffect, useState } from 'react';
import AdminLayout from './AdminLayout';
import api from '../../services/api';
import { Monitor, Trash2, Plus, Link as LinkIcon, Edit, X, Save } from 'lucide-react';

const KioskManager = () => {
  const [kiosks, setKiosks] = useState([]);
  const [loading, setLoading] = useState(true);
  
  // Modal State
  const [showModal, setShowModal] = useState(false);
  const [isEditing, setIsEditing] = useState(false);

  const [form, setForm] = useState({ 
      slug: '', 
      target_icao: '', 
      subscriber_name: '', 
      default_profile: 'small',
      weather_override_icao: '',
      title_override: '',
      show_raw_metar: true,
      show_notams: true,
      show_facility_message: false,
      custom_message_html: ''
  });

  const fetchKiosks = async () => {
    try {
      const res = await api.get("/api/kiosk/list");
      setKiosks(res);
    } catch (e) { console.error(e); } 
    finally { setLoading(false); }
  };

  useEffect(() => { fetchKiosks(); }, []);

  // Open Modal for New Entry
  const handleCreate = () => {
      setForm({ 
          slug: '', target_icao: '', subscriber_name: '', default_profile: 'small',
          weather_override_icao: '', title_override: '',
          show_raw_metar: true, show_notams: true, show_facility_message: false, custom_message_html: ''
      });
      setIsEditing(false);
      setShowModal(true);
  };

  // Open Modal for Edit
  const handleEdit = (kiosk) => {
      // Parse Config JSON safely
      let conf = {};
      try {
          if (kiosk.config_options) conf = JSON.parse(kiosk.config_options);
      } catch (e) { console.error("JSON Parse Error", e); }

      setForm({
          slug: kiosk.slug,
          target_icao: kiosk.target_icao,
          subscriber_name: kiosk.subscriber_name,
          default_profile: kiosk.default_profile,
          weather_override_icao: kiosk.weather_override_icao || '',
          title_override: kiosk.title_override || '',
          show_raw_metar: conf.show_raw_metar ?? true,
          show_notams: conf.show_notams ?? true,
          show_facility_message: conf.show_facility_message ?? false,
          custom_message_html: conf.custom_message_html || ''
      });
      setIsEditing(true);
      setShowModal(true);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
        await api.post("/api/kiosk/add", form);
        setShowModal(false);
        fetchKiosks();
    } catch (e) { alert("Failed to save kiosk"); }
  };

  const handleRemove = async (slug) => {
      if(!confirm("Delete Kiosk Profile?")) return;
      await api.delete(`/api/kiosk/remove/${slug}`);
      fetchKiosks();
  };

  return (
    <AdminLayout>
      <div className="flex flex-col md:flex-row justify-between items-center mb-8 gap-4">
        <div>
            <h1 className="text-2xl font-bold text-white">Kiosk Profiles</h1>
            <p className="text-neutral-500 text-sm">Manage client-specific kiosk URLs.</p>
        </div>
        <button 
            onClick={handleCreate} 
            className="bg-blue-600 hover:bg-blue-500 text-white font-bold py-2 px-6 rounded-full flex items-center gap-2 shadow-lg shadow-blue-900/20 transition-all"
        >
            <Plus size={18} /> Create Profile
        </button>
      </div>

      {/* LIST TABLE */}
      <div className="bg-neutral-900/50 border border-neutral-800 rounded-xl overflow-hidden shadow-xl">
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
                    <tr key={k.slug} className="hover:bg-neutral-800/50 transition-colors">
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
                                <LinkIcon size={12} /> Open
                            </a>
                        </td>
                        <td className="p-4 text-right">
                            <button onClick={() => handleEdit(k)} className="text-blue-500 hover:text-white transition-colors mr-3" title="Edit Profile">
                                <Edit size={16} />
                            </button>
                            <button onClick={() => handleRemove(k.slug)} className="text-red-500 hover:text-white transition-colors" title="Delete Profile">
                                <Trash2 size={16} />
                            </button>
                        </td>
                    </tr>
                ))}
                {kiosks.length === 0 && !loading && <tr><td colSpan={4} className="p-8 text-center italic">No profiles found.</td></tr>}
            </tbody>
        </table>
      </div>

      {/* EDIT / CREATE MODAL */}
      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md animate-fade-in">
            <div className="bg-neutral-900 border border-neutral-800 w-full max-w-2xl rounded-xl shadow-2xl relative flex flex-col max-h-[90vh]">
                
                {/* Modal Header */}
                <div className="px-6 py-4 border-b border-neutral-800 flex justify-between items-center bg-neutral-900">
                    <h3 className="text-white font-bold uppercase tracking-widest text-sm flex items-center gap-2">
                        {isEditing ? <Edit size={16} className="text-blue-500"/> : <Plus size={16} className="text-green-500"/>}
                        {isEditing ? `Edit Profile: ${form.slug}` : "New Kiosk Profile"}
                    </h3>
                    <button onClick={() => setShowModal(false)} className="text-neutral-500 hover:text-white transition-colors">
                        <X size={20} />
                    </button>
                </div>

                {/* Modal Body */}
                <div className="p-6 overflow-y-auto">
                    <form onSubmit={handleSubmit} className="space-y-5">
                        
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                            <div>
                                <label className="block text-xs font-bold text-neutral-500 mb-1 uppercase">Subscriber Name</label>
                                <input required className="w-full bg-black border border-neutral-700 rounded p-3 text-white focus:border-blue-500 outline-none transition-colors" 
                                    placeholder="e.g. Bob's Flight School" 
                                    value={form.subscriber_name} 
                                    onChange={e => setForm({...form, subscriber_name: e.target.value})} 
                                />
                            </div>
                            <div>
                                <label className="block text-xs font-bold text-neutral-500 mb-1 uppercase">URL Slug (ID)</label>
                                <input required 
                                    className={`w-full border rounded p-3 text-white font-mono focus:border-blue-500 outline-none transition-colors ${isEditing ? 'bg-neutral-800 border-neutral-700 text-neutral-400 cursor-not-allowed' : 'bg-black border-neutral-700'}`}
                                    placeholder="e.g. bobs-flight-school" 
                                    value={form.slug} 
                                    readOnly={isEditing}
                                    onChange={e => setForm({...form, slug: e.target.value.toLowerCase().replace(/\s+/g, '-')})} 
                                />
                                {isEditing && <p className="text-[10px] text-neutral-500 mt-1">Slug cannot be changed while editing. Create a new profile to rename.</p>}
                            </div>
                        </div>
                        
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                            <div>
                                <label className="block text-xs font-bold text-neutral-500 mb-1 uppercase">Target Airport (ICAO)</label>
                                <input required className="w-full bg-black border border-neutral-700 rounded p-3 text-white font-mono uppercase focus:border-blue-500 outline-none" 
                                    placeholder="e.g. K123" 
                                    value={form.target_icao} 
                                    onChange={e => setForm({...form, target_icao: e.target.value.toUpperCase()})} 
                                />
                            </div>
                            <div>
                                <label className="block text-xs font-bold text-neutral-500 mb-1 uppercase">Weather Source (Optional)</label>
                                <input className="w-full bg-black border border-neutral-700 rounded p-3 text-white font-mono uppercase focus:border-blue-500 outline-none" 
                                    placeholder="e.g. KBOS (Leave empty for Auto)" 
                                    value={form.weather_override_icao} 
                                    onChange={e => setForm({...form, weather_override_icao: e.target.value.toUpperCase()})} 
                                />
                            </div>
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                            <div>
                                <label className="block text-xs font-bold text-neutral-500 mb-1 uppercase">Default Aircraft Profile</label>
                                <select className="w-full bg-black border border-neutral-700 rounded p-3 text-white focus:border-blue-500 outline-none appearance-none cursor-pointer" 
                                    value={form.default_profile} 
                                    onChange={e => setForm({...form, default_profile: e.target.value})}
                                >
                                    <option value="small">Small (Max 15kts)</option>
                                    <option value="medium">Medium (Max 20kts)</option>
                                    <option value="large">Large (Max 30kts)</option>
                                </select>
                            </div>
                            <div>
                                <label className="block text-xs font-bold text-neutral-500 mb-1 uppercase">Title Override (Optional)</label>
                                <input className="w-full bg-black border border-neutral-700 rounded p-3 text-white focus:border-blue-500 outline-none" 
                                    placeholder="Custom Page Title" 
                                    value={form.title_override} 
                                    onChange={e => setForm({...form, title_override: e.target.value})} 
                                />
                            </div>
                        </div>

                        {/* CONFIGURATION & FACILITY MESSAGE */}
                        <div className="border-t border-neutral-800 pt-5 mt-2">
                            <h4 className="text-white text-xs font-bold uppercase mb-4">Display Configuration</h4>
                            
                            <div className="flex gap-4 mb-4">
                                <label className="flex items-center gap-2 bg-neutral-800 px-3 py-2 rounded cursor-pointer border border-neutral-700 select-none">
                                    <input type="checkbox" checked={form.show_facility_message} onChange={e => setForm({...form, show_facility_message: e.target.checked})} />
                                    <span className="text-xs font-bold text-white">Facility Msg</span>
                                </label>
                                <label className="flex items-center gap-2 bg-neutral-800 px-3 py-2 rounded cursor-pointer border border-neutral-700 select-none">
                                    <input type="checkbox" checked={form.show_raw_metar} onChange={e => setForm({...form, show_raw_metar: e.target.checked})} />
                                    <span className="text-xs font-bold text-white">Raw Metar</span>
                                </label>
                                <label className="flex items-center gap-2 bg-neutral-800 px-3 py-2 rounded cursor-pointer border border-neutral-700 select-none">
                                    <input type="checkbox" checked={form.show_notams} onChange={e => setForm({...form, show_notams: e.target.checked})} />
                                    <span className="text-xs font-bold text-white">NOTAMs</span>
                                </label>
                            </div>

                            {form.show_facility_message && (
                                <div>
                                    <label className="block text-xs font-bold text-neutral-500 mb-1 uppercase">Facility Message (HTML Supported)</label>
                                    <textarea 
                                        className="w-full bg-black border border-neutral-700 rounded p-3 text-white focus:border-blue-500 outline-none font-mono text-xs h-32" 
                                        placeholder="<p>Welcome to <b>Bob's Flight School</b></p>"
                                        value={form.custom_message_html} 
                                        onChange={e => setForm({...form, custom_message_html: e.target.value})} 
                                    />
                                </div>
                            )}
                        </div>

                        {/* Actions */}
                        <div className="pt-4 flex justify-end gap-3 border-t border-neutral-800 mt-4">
                            <button 
                                type="button" 
                                onClick={() => setShowModal(false)}
                                className="px-6 py-3 text-sm font-bold text-neutral-500 hover:text-white transition-colors"
                            >
                                CANCEL
                            </button>
                            <button 
                                type="submit" 
                                className="bg-blue-600 hover:bg-blue-500 text-white font-bold py-3 px-8 rounded-lg flex items-center gap-2 transition-all shadow-lg"
                            >
                                <Save size={18} /> {isEditing ? "SAVE CHANGES" : "CREATE PROFILE"}
                            </button>
                        </div>

                    </form>
                </div>
            </div>
        </div>
      )}

    </AdminLayout>
  );
};

export default KioskManager;