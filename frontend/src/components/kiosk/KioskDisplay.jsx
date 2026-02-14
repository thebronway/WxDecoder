import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import api from '../../services/api';
import Bubble from '../Bubble';
import { AlertTriangle, Clock, Plane, Info } from 'lucide-react';

const NOTAMScroller = ({ notams }) => {
    if (!notams || notams.length === 0) return <div className="p-4 text-gray-500 h-full bg-black/40 rounded-lg">No NOTAMs.</div>;

    return (
        <div className="relative h-full overflow-hidden bg-black/40 rounded-lg">
            <div className="absolute inset-0 z-10 pointer-events-none bg-gradient-to-b from-neutral-900/20 via-transparent to-neutral-900/20 h-full"></div>
            <div className="animate-marquee py-4 space-y-6 min-h-full">
                {[...notams, ...notams].map((n, i) => (
                    <div key={i} className="px-6">
                        <p className="text-green-400 font-mono text-sm leading-relaxed uppercase whitespace-pre-wrap border-l-4 border-green-700 pl-4">
                            {n}
                        </p>
                    </div>
                ))}
            </div>
            <style>{`
                @keyframes marquee {
                    0% { transform: translateY(0); }
                    100% { transform: translateY(-50%); }
                }
                .animate-marquee {
                    animation: marquee ${Math.max(notams.length * 10, 30)}s linear infinite;
                }
            `}</style>
        </div>
    );
};

const BriefingScroller = ({ analysis, isDifferent, source, target }) => {
    const [activeIndex, setActiveIndex] = useState(0);
    const [transitionDuration, setTransitionDuration] = useState(2000);
    const [offsets, setOffsets] = useState([]);
    const [shouldScroll, setShouldScroll] = useState(false);
    
    const containerRef = React.useRef(null);

    // Define sections data to keep JSX clean and allowing duplication
    const sections = [
        {
            id: 'weather',
            title: `CURRENT WEATHER ${isDifferent ? `(${source})` : ""}`,
            content: analysis.summary_weather
        },
        {
            id: 'crosswind',
            title: `CROSSWIND`,
            content: analysis.summary_crosswind
        },
        {
            id: 'airspace',
            title: `AIRSPACE`,
            content: analysis.summary_airspace
        },
        {
            id: 'notams',
            title: `NOTABLE NOTAMS`,
            content: analysis.summary_notams
        }
    ];

    // 1. Measure and determine if we need to scroll (overflow check)
    React.useLayoutEffect(() => {
        const container = containerRef.current;
        if (!container) return;

        // Reset to initial state when data changes
        setTransitionDuration(0);
        setActiveIndex(0);

        const timeout = setTimeout(() => {
            const parent = container.parentElement;
            // Measure height of the "Unique" content (first 4 items)
            // We approximate this by taking the container height. 
            // If we are already looping, this might be large, but the logic holds:
            // If the content fits, we don't need to loop.
            
            // To be safe, we check if the offsets of the last unique item exceed view height.
            const children = Array.from(container.children);
            const uniqueCount = sections.length;
            
            // If we haven't rendered duplicate yet, children.length is 4.
            // If we have, it is 5. We only care about the first 4.
            const lastUniqueItem = children[uniqueCount - 1];
            
            if (lastUniqueItem) {
                const contentBottom = lastUniqueItem.offsetTop + lastUniqueItem.offsetHeight;
                const viewHeight = parent.offsetHeight;
                setShouldScroll(contentBottom > viewHeight);
            }
        }, 100);

        return () => clearTimeout(timeout);
    }, [analysis]);

    // 2. Measure Offsets (Whenever render changes)
    React.useLayoutEffect(() => {
        const container = containerRef.current;
        if (!container) return;
        
        // Measure all children (including duplicate if present)
        const newOffsets = Array.from(container.children).map(child => child.offsetTop);
        setOffsets(newOffsets);
    }, [shouldScroll, analysis]);


    // 3. The Infinite Loop Timer
    useEffect(() => {
        if (!shouldScroll || offsets.length === 0) return;

        const interval = setInterval(() => {
            // 1. Enable animation
            setTransitionDuration(2000);
            
            // 2. Move to next index
            requestAnimationFrame(() => {
                setActiveIndex(prev => {
                    // Safety check: if we somehow went past, reset now
                    if (prev >= sections.length) return 0;
                    return prev + 1;
                });
            });
        }, 8000);

        return () => clearInterval(interval);
    }, [offsets, shouldScroll, sections.length]);


    // 4. The "Snap" Logic (Teleport from Duplicate to Start)
    useEffect(() => {
        // Snap point: When we reach the start of the duplicate set
        if (shouldScroll && activeIndex === sections.length) {
            // Wait slightly longer than the transition (2200ms) to ensure it is fully settled
            const timeout = setTimeout(() => {
                // Disable transition instantly
                setTransitionDuration(0);
                // Teleport to index 0 (Visual Match)
                setActiveIndex(0);
                // We DO NOT restore duration here; the Interval will handle it before the next move.
            }, 2200);
            return () => clearTimeout(timeout);
        }
    }, [activeIndex, shouldScroll, sections.length]);


    // Prepare list: Double Buffer (Render twice for seamless loop)
    const itemsToRender = shouldScroll ? [...sections, ...sections] : sections;
    
    const currentTranslateY = (offsets[activeIndex] !== undefined) ? -offsets[activeIndex] : 0;

    return (
        <div className="flex-1 min-h-0 relative overflow-hidden flex flex-col">
             <div 
                ref={containerRef}
                className="ease-in-out pb-24"
                style={{ 
                    transform: `translateY(${currentTranslateY}px)`,
                    transitionDuration: `${transitionDuration}ms`,
                    transitionProperty: 'transform'
                }}
             >
                {itemsToRender.map((section, index) => (
                    <div key={`${section.id}-${index}`} className="mb-16">
                        <h3 className="text-blue-400 font-bold uppercase tracking-widest mb-2 border-b border-blue-900/30 w-fit">
                            {section.title}
                        </h3>
                        <p className="text-xl leading-relaxed text-gray-200">
                            {section.content || "No data."}
                        </p>
                    </div>
                ))}
             </div>
        </div>
    );
};

const TimelineCard = ({ title, summary }) => (
    <div className="bg-neutral-800 border border-neutral-700 rounded-xl p-4 flex flex-col h-full relative overflow-hidden">
        <div className="border-b border-neutral-700 pb-2 mb-2 shrink-0">
             <span className="text-blue-400 font-bold text-sm md:text-base block uppercase tracking-widest truncate">
                {title}
             </span>
        </div>
        <p className="text-gray-200 text-base md:text-lg leading-relaxed overflow-y-auto">
            {summary || "No Forecast Available"}
        </p>
    </div>
);

const FacilityMessage = ({ htmlContent, expanded }) => (
    <div className={`bg-neutral-800/80 border border-neutral-700 rounded-xl p-5 shrink-0 shadow-lg flex flex-col overflow-hidden relative ${expanded ? 'flex-1' : 'min-h-[10rem] h-auto'}`}>
        <div className="prose prose-invert prose-sm max-w-none leading-snug h-full w-full" dangerouslySetInnerHTML={{ __html: htmlContent }} />
    </div>
);

// Helper for METAR Time Parsing
const getMetarTime = (metarString, timezone) => {
  if (!metarString) return null;
  const match = metarString.match(/\b(\d{2})(\d{2})(\d{2})Z\b/);
  if (!match) return null;

  const [_, day, hour, minute] = match;
  const now = new Date();
  const date = new Date(Date.UTC(now.getUTCFullYear(), now.getUTCMonth(), parseInt(day), parseInt(hour), parseInt(minute)));
  
  if (parseInt(day) > now.getUTCDate() + 1) {
      date.setUTCMonth(date.getUTCMonth() - 1);
  }

  const utcString = date.toLocaleTimeString('en-US', { timeZone: 'UTC', hour: '2-digit', minute: '2-digit', hour12: false });
  const localString = date.toLocaleTimeString('en-US', { timeZone: timezone, hour: '2-digit', minute: '2-digit', hour12: false, timeZoneName: 'short' });

  return { utc: `${utcString}Z`, local: localString };
};

const KioskDisplay = () => {
    const { slug } = useParams();
    const navigate = useNavigate();
    
    // State
    const [config, setConfig] = useState(null);
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [lastMetarRaw, setLastMetarRaw] = useState(null);
    const [currentTime, setCurrentTime] = useState(new Date());
    const [weatherSource, setWeatherSource] = useState(null);

    const PROFILE_LIMITS = {
        small: "15KTS",
        medium: "20KTS",
        large: "30KTS"
    };

    // 1. Initial Authorization & Config Load
    useEffect(() => {
        console.log("🔄 Kiosk useEffect triggering for slug:", slug);
        const init = async () => {
            try {
                console.log("🚀 Fetching config for:", slug);
                // Fetch Config by Slug
                const conf = await api.get(`/api/kiosk/config/${slug}`);
                console.log("✅ Config received:", conf);
                setConfig(conf);
                
                // Trigger initial analysis using the config's defaults
                loadAnalysis(conf.default_profile, false, conf); 
            } catch (e) {
                console.error("Config Load Error", e);
                setLoading(false);
            }
        };
        init();
    }, [slug]);

    // 2. Clock & Wake Lock
    useEffect(() => {
        const t = setInterval(() => setCurrentTime(new Date()), 1000);

        let wakeLock = null;
        const requestWakeLock = async () => {
            if ('wakeLock' in navigator) {
                try { wakeLock = await navigator.wakeLock.request('screen'); } 
                catch (err) { console.log(err); }
            }
        };
        requestWakeLock();

        return () => {
            clearInterval(t);
            wakeLock?.release();
        };
    }, []);

    // 3. Poller
    useEffect(() => {
        const poller = setInterval(async () => {
            if (!config) return;

            try {
                // Peek the TARGET icao from config
                const targetIcao = config.target_icao;
                const wxSource = config.weather_override_icao || weatherSource;
                
                const query = wxSource ? `?source=${wxSource}` : "";
                const res = await api.get(`/api/kiosk/peek/${targetIcao}${query}`);
                
                if (res.status === "success" && res.raw_metar) {
                    const cleanNew = res.raw_metar.replace(/\s/g, '');
                    const cleanOld = lastMetarRaw ? lastMetarRaw.replace(/\s/g, '') : '';
                    
                    if (cleanNew !== cleanOld) {
                        console.log("KIOSK: New METAR detected. Refreshing AI...");
                        // Use config.default_profile instead of 'profile'
                        loadAnalysis(config.default_profile, true, config);
                    }
                }
            } catch (e) { console.error("Poll failed", e); }
        }, 60 * 1000); 

        return () => clearInterval(poller);
    }, [config, lastMetarRaw]);

    const loadAnalysis = async (pSize, force = false, conf = config) => {
        if (!conf) return;
        setLoading(true);
        try {
            const res = await api.post("/api/analyze", { 
                icao: conf.target_icao, 
                plane_size: pSize,
                force: force,
                weather_override: conf.weather_override_icao // Pass the override
            });
            setData(res);
            setLastMetarRaw(res.raw_data?.metar);
            setWeatherSource(res.raw_data?.weather_source);
            document.title = `${conf.subscriber_name} | WxDecoder`;
        } catch (e) {
            console.error("Analysis load failed", e);
        } finally {
            setLoading(false);
        }
    };

    // LOADING STATE
    if (loading) {
        return (
            <div className="w-screen h-screen bg-black flex flex-col items-center justify-center space-y-8">
                <img src="/logo.webp" className="w-64 md:w-96 animate-pulse" />
                <p className="text-blue-500 font-mono text-2xl tracking-[0.5em] animate-pulse">REFRESHING DATA...</p>
            </div>
        );
    }

    // ERROR STATE (Prevents White Screen Crash)
    if (!data) {
        return (
            <div className="w-screen h-screen bg-neutral-900 flex flex-col items-center justify-center space-y-4 text-center p-8">
                <AlertTriangle className="w-16 h-16 text-red-500" />
                <h1 className="text-3xl font-bold text-white">Connection Lost</h1>
                <p className="text-gray-400">Unable to load kiosk configuration or weather data.</p>
                <div className="text-xs font-mono text-red-400 bg-red-900/20 p-4 rounded border border-red-900/50 mt-4">
                    DEBUG: Slug="{slug}" | Config={config ? "OK" : "MISSING"}
                </div>
            </div>
        );
    }

    const { analysis, raw_data } = data;
    const timeline = analysis.timeline || {};
    const metarTimes = getMetarTime(raw_data.metar, data.airport_tz || 'UTC');

    const target = config?.target_icao || "";
    const source = raw_data.weather_source ? raw_data.weather_source.toUpperCase() : "";
    const isDifferent = source && target && source !== target && source !== "K" + target;

    return (
        <div className="w-screen h-screen bg-neutral-900 text-white overflow-hidden font-sans p-6 grid grid-rows-[auto_1fr] gap-6 selection:bg-none cursor-none">
            
            {/* HEADER ROW */}
            <div className="flex justify-between items-end border-b-2 border-neutral-800 pb-4 shrink-0">
                <div className="flex items-center gap-10">
                    <img src="/logo.webp" className="h-20 w-auto object-contain" />
                    <div className="min-w-0 flex-1 pr-6">
                        <h1 className="text-4xl md:text-6xl font-black tracking-tighter text-white leading-none truncate whitespace-nowrap">
                            {config?.title_override || data.airport_name}
                        </h1>
                        <div className="flex items-center gap-6 mt-3">
                        <span className="bg-blue-900/30 text-blue-400 border border-blue-800 px-3 py-1 rounded text-xl font-bold font-mono">
                            {config?.target_icao}
                        </span>

                            {/* SPECI Indicator */}
                            {raw_data.metar?.includes("SPECI") && (
                                <span className="bg-yellow-900/40 text-yellow-500 border border-yellow-700/50 px-3 py-1 rounded text-xl font-bold font-mono animate-pulse shadow-[0_0_10px_rgba(234,179,8,0.2)]">
                                    SPECI
                                </span>
                            )}                           
                            
                            {/* METAR Source Bubble (If different or distant) */}
                            {(isDifferent || raw_data.weather_dist > 0) && (
                                <div className="inline-flex items-center justify-center gap-2 text-sm font-mono text-yellow-200 bg-yellow-900/30 px-4 py-1 rounded-full border border-yellow-700/50 animate-fade-in">
                                     <Info className="w-4 h-4 text-yellow-500" />
                                     <span className="text-[10px] uppercase tracking-widest text-yellow-500 font-bold mr-1">METAR Source:</span>
                                     <span>{source} {raw_data.weather_dist > 0 ? `(${raw_data.weather_dist}nm)` : ""}</span>
                                </div>
                            )}

                            {/* METAR Time Bubble */}
                            {metarTimes && (
                                <div className="inline-flex items-center justify-center gap-2 text-sm font-mono text-blue-200 bg-blue-900/20 px-4 py-1 rounded-full border border-blue-900/30">
                                     <Clock className="w-4 h-4 text-blue-500" />
                                     <span className="text-[10px] uppercase tracking-widest text-blue-500 font-bold mr-1">METAR Generated:</span>
                                     <span className="text-blue-500 font-bold">UTC</span> {metarTimes.utc}
                                     <span className="w-px h-3 bg-blue-800/50 mx-1"></span>
                                     <span className="text-blue-500 font-bold">LCL</span> {metarTimes.local}
                                </div>
                            )}

                            {/* Grey Profile Bubble */}
                            <div className="inline-flex items-center justify-center gap-2 text-sm font-mono text-gray-300 bg-neutral-800/50 px-4 py-1 rounded-full border border-neutral-700/50">
                                 <Plane className="w-4 h-4 text-gray-500" />
                                 <span className="text-gray-500 font-bold">PROFILE</span> {config?.default_profile?.toUpperCase()} (MAX: {PROFILE_LIMITS[config?.default_profile] || "--"})
                            </div>
                        </div>
                    </div>
                </div>
                
                {/* Clock */}
                <div className="text-right">
                    <div className="text-6xl font-mono font-bold text-gray-200">
                        {currentTime.toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute:'2-digit' })}
                        <span className="text-2xl text-neutral-500 ml-2">LCL</span>
                    </div>
                    <div className="text-xl text-blue-500 font-mono font-bold mt-1">
                        {currentTime.toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute:'2-digit', timeZone: 'UTC' })}Z
                    </div>
                </div>
            </div>

            {/* MAIN GRID Content */}
            <div className="grid grid-cols-12 gap-8 h-full min-h-0">
                
                {/* LEFT COL: AI Briefing & Bubbles (8 Cols) */}
                <div className="col-span-8 flex flex-col gap-4 h-full min-h-0">
                    
                    {/* 1. Current Conditions Bubbles (Standard Labels) - Auto Height, Flex-None */}
                    <div className="grid grid-cols-4 gap-4 flex-none h-40">
                        <Bubble label="CATEGORY" value={analysis.flight_category} highlight={true} />
                        {/* Split Wind Bubble */}
                        <Bubble 
                            label="WIND" 
                            value={analysis.bubbles?.wind || "--"} 
                            subLabel={`CROSSWIND RWY ${analysis.bubbles?.rwy || "??"}`}
                            subValue={analysis.bubbles?.x_wind || "--"}
                            risk={analysis.crosswind_status} 
                        />
                        <Bubble label="CEILING" value={analysis.bubbles?.ceiling} />
                        <Bubble label="VISIBILITY" value={analysis.bubbles?.visibility} />
                    </div>

                    {/* 2. Forecast Bubbles (TAF) - Hide if NO TAF AVAILABLE */ }
                    {(raw_data.taf && !raw_data.taf.includes("No TAF available")) && (
                        <div className="grid grid-cols-2 gap-4 flex-none">
                            <TimelineCard 
                                title={`Weather ${timeline.forecast_1?.time_label || "Upcoming"}${isDifferent ? ` (${source})` : ""}`}
                                summary={timeline.forecast_1?.summary || timeline.forecast_1} 
                            />
                            <TimelineCard 
                                title={
                                    (timeline.forecast_2 === "NO_TAF" || timeline.forecast_2?.time_label === "NO_TAF") 
                                    ? "NO ADDITIONAL TAF AVAILABLE"
                                    : `Weather ${timeline.forecast_2?.time_label || "Outlook"}${isDifferent ? ` (${source})` : ""}`
                                }
                                summary={
                                    (timeline.forecast_2 === "NO_TAF" || timeline.forecast_2?.summary === "NO_TAF" || timeline.forecast_2?.summary === "NO_TAF.")
                                    ? "--"
                                    : (timeline.forecast_2?.summary || timeline.forecast_2)
                                } 
                            />
                        </div>
                    )}

                    {/* 3. AI Briefing Box - Takes Remaining Space */}
                    <div className="bg-neutral-800/40 border border-neutral-700/50 rounded-2xl p-6 flex-1 min-h-0 relative shadow-2xl flex flex-col overflow-hidden">
                         <h2 className="text-neutral-500 text-xs font-bold uppercase tracking-widest mb-4 border-b border-neutral-700 pb-2 flex items-center gap-2 shrink-0">
                            Briefing Overview
                         </h2>

                         {/* NEW SCROLLER COMPONENT */}
                         <BriefingScroller 
                            analysis={analysis} 
                            isDifferent={isDifferent} 
                            source={source} 
                            target={target} 
                         />
                         
                         {/* Warnings Footer */}
                         <div className="absolute bottom-0 left-0 right-0 bg-neutral-900/95 p-3 border-t border-red-900/50 flex items-center justify-between gap-4 overflow-hidden z-20">
                            <div className="flex gap-4 overflow-x-auto whitespace-nowrap">
                                {analysis.airspace_warnings.map((w,i) => (
                                    <span key={i} className="text-red-400 font-bold flex items-center gap-2 text-base">
                                        <AlertTriangle size={18} /> {w}
                                    </span>
                                ))}
                                {(!analysis.airspace_warnings?.length) && (
                                    <span className="text-green-500/50 font-bold flex items-center gap-2">
                                        NO PERMANENT AIRSPACE RESTRICTIONS DETECTED
                                    </span>
                                )}
                            </div>
                            <span className="text-orange-500 font-bold text-xs uppercase tracking-widest shrink-0">
                                ALWAYS CHECK DYNAMIC TFRS AT TFR.FAA.GOV
                            </span>
                         </div>
                    </div>
                </div>

                <div className="col-span-4 flex flex-col gap-4 h-full min-h-0">
                    
                    {config?.config?.show_facility_message && (
                        <FacilityMessage 
                            htmlContent={config?.config?.custom_message_html} 
                            expanded={!config?.config?.show_raw_metar && !config?.config?.show_notams}
                        />
                    )}

                    {config?.config?.show_raw_metar !== false && (
                        <div className="bg-black border border-neutral-800 rounded-xl p-5 shrink-0 shadow-lg flex-none">
                            <h3 className="text-gray-500 font-bold text-xs uppercase mb-2">Raw METAR</h3>
                            <p className="font-mono text-green-400 text-lg leading-tight break-words">
                                {raw_data.metar}
                            </p>
                            
                            <div className="my-4 border-t border-neutral-900"></div>
                            
                            <h3 className="text-gray-500 font-bold text-xs uppercase mb-2">Terminal Forecast</h3>
                            <p className="font-mono text-blue-400 text-lg leading-tight whitespace-pre-wrap">
                                {raw_data.taf ? raw_data.taf.replace(/(FM|BECMG|TEMPO)/g, '\n$1') : "No TAF Available"}
                            </p>
                        </div>
                    )}

                    {config?.config?.show_notams !== false && (
                        <div className="bg-neutral-900 border border-neutral-800 rounded-xl flex-1 min-h-0 flex flex-col overflow-hidden relative shadow-inner">
                            <div className="bg-neutral-800 p-3 z-20 shadow-md shrink-0">
                                <h3 className="text-orange-500 font-bold uppercase tracking-widest text-center">Active NOTAMs</h3>
                            </div>
                            <div className="text-sm flex-1 min-h-0 relative"> 
                                <NOTAMScroller notams={raw_data.notams} />
                            </div>
                        </div>
                    )}

                    <div className="bg-neutral-800 border border-neutral-700 rounded-lg p-3 shrink-0">
                        <p className="text-xs text-gray-300 font-medium flex items-center justify-center gap-1 text-center">
                            <AlertTriangle className="w-4 h-4 text-red-500 shrink-0" />
                            <span className="font-bold text-red-500">DISCLAIMER:</span> 
                            <span>AI normalizes data and can make errors. Always verify with official sources.</span>
                        </p>
                    </div>

                </div>
            </div>
        </div>
    );
};

export default KioskDisplay;