"use client";

import {useEffect, useRef, useState} from 'react';
import DesktopWindow from './DesktopWindow';
import {HUB_CHANNEL, HUB_ORIGIN, hubOriginForPreview, readHubState, type HubPath, type HubState} from './safariBridge';
import './desktopSafari.css';

type Props = {
  active: boolean; foreground: boolean; minimized: boolean; zIndex: number;
  onActivate: () => void; onMinimize: () => void; onClose: () => void;
};
type IconName = 'sidebar' | 'back' | 'forward' | 'reload' | 'lock' | 'share' | 'book' | 'home';
function Icon({name}: {name: IconName}) {
  const paths: Record<IconName,string> = {
    sidebar:'M3 4h18v16H3zM9 4v16M5.5 8h1M5.5 11h1M5.5 14h1',
    back:'m14 5-7 7 7 7', forward:'m10 5 7 7-7 7',
    reload:'M20 9a8 8 0 1 0 0 7M20 3v6h-6', lock:'M6 11h12v10H6zM8 11V7a4 4 0 0 1 8 0v4',
    share:'M8 9H4v12h16V9h-4M12 15V2m-4 4 4-4 4 4',
    book:'M12 5C8 2 4 3 2 4v16c3-2 7-2 10 0 3-2 7-2 10 0V4c-3-2-7-2-10 1Zm0 0v15',
    home:'m3 11 9-8 9 8M5 10v11h14V10M10 21v-7h4v7',
  };
  return <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.65" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d={paths[name]}/></svg>;
}
const initialState: HubState = {path:'/', title:'Research Work — Brian Zeng', canBack:false, canForward:false};

export default function DesktopSafari(props: Props) {
  const frame = useRef<HTMLIFrameElement>(null);
  const callbacks = useRef(props); callbacks.current = props;
  const [origin, setOrigin] = useState<string | null>(null);
  const [parentOrigin, setParentOrigin] = useState('');
  const [frameSource, setFrameSource] = useState<string | undefined>();
  const [page, setPage] = useState<HubState>(initialState);
  const [ready, setReady] = useState(false);
  const readyRef = useRef(false);
  const [failed, setFailed] = useState(false);
  const [revision, setRevision] = useState(0);
  const [sidebar, setSidebar] = useState(false);
  const [popover, setPopover] = useState<'share' | 'pages' | null>(null);
  const [saved, setSaved] = useState<HubPath[]>([]);
  const [notice, setNotice] = useState('');
  const [zoom, setZoom] = useState(1);

  useEffect(() => {
    const hub = hubOriginForPreview(window.location.hostname, window.location.search);
    setOrigin(hub);
    setParentOrigin(window.location.origin);
    setFrameSource(`${hub}/?embed=safari&parentOrigin=${encodeURIComponent(window.location.origin)}`);
  }, []);
  useEffect(() => {
    if (!origin) return;
    readyRef.current = false; setReady(false); setFailed(false);
    function receive(event: MessageEvent) {
      if (event.origin !== origin || event.source !== frame.current?.contentWindow || !event.data || event.data.channel !== HUB_CHANNEL) return;
      const state = readHubState(event.data);
      if (state) { readyRef.current = true; setReady(true); setFailed(false); setPage(state); }
      else if (event.data.type === 'focus') { callbacks.current.onActivate(); setPopover(null); }
      else if (event.data.type === 'blocked') setNotice('This Safari window is limited to the research gallery.');
    }
    window.addEventListener('message', receive);
    const hello = () => frame.current?.contentWindow?.postMessage({channel:HUB_CHANNEL,type:'hello'}, origin);
    const handshake = window.setInterval(() => { if (!readyRef.current) hello(); }, 500);
    const timeout = window.setTimeout(() => { if (!readyRef.current) setFailed(true); }, 10000);
    return () => { window.removeEventListener('message', receive); clearInterval(handshake); clearTimeout(timeout); };
  }, [origin, revision]);
  useEffect(() => {
    if (!notice) return;
    const timer = setTimeout(() => setNotice(''), 3500);
    return () => clearTimeout(timer);
  }, [notice]);
  function send(type: 'navigate' | 'back' | 'forward' | 'reload', path?: HubPath) {
    if (!ready || !origin) return;
    frame.current?.contentWindow?.postMessage({channel:HUB_CHANNEL,type,...(path ? {path} : {})},origin);
    setPopover(null);
  }
  function reload() {
    if (!origin) return;
    if (ready) { send('reload'); return; }
    setFrameSource(`${origin}${page.path}?embed=safari&parentOrigin=${encodeURIComponent(parentOrigin)}`);
    setRevision(value => value + 1); setPopover(null);
  }
  function navigate(path: HubPath) { send('navigate',path); }
  async function copyLink() {
    try { await navigator.clipboard.writeText(HUB_ORIGIN + page.path); setNotice('Link copied'); }
    catch { setNotice('Clipboard unavailable. The page address is shown above.'); }
    setPopover(null);
  }
  const button = (name: IconName, label: string, action: () => void, disabled=false, pressed?: boolean) =>
    <button type="button" title={label} aria-label={label} disabled={disabled} aria-pressed={pressed} onClick={action}><Icon name={name}/></button>;

  return <DesktopWindow {...props} title="Safari" className="mac-safari-window" initialFrame={{x:.085,y:.07,width:.83,height:.83}} minimumSize={{width:380,height:280}}
    titlebar={<div className="safari-toolbar" onKeyDown={event => { if (event.key === 'Escape') setPopover(null); }}>
      <div className="safari-control-group">
        {button('sidebar',sidebar?'Hide sidebar':'Show sidebar',()=>setSidebar(!sidebar),false,sidebar)}
      </div>
      <div className="safari-control-group safari-history">
        {button('back','Back',()=>send('back'),!ready||!page.canBack)}
        {button('forward','Forward',()=>send('forward'),!ready||!page.canForward)}
      </div>
      <div className="safari-address" data-window-no-drag>
        {button('book','Page options',()=>setPopover(popover==='pages'?null:'pages'))}
        <a className="safari-address-display" href={HUB_ORIGIN + page.path} target="_blank" rel="noopener noreferrer" aria-label="Open current page in a new browser tab"><Icon name="lock"/><span>gallery.brianbzeng.com{page.path==='/'?'':page.path}</span></a>
        {button('reload','Reload page',reload)}
      </div>
      <div className="safari-control-group safari-tools">
        {button('share','Share page',()=>setPopover(popover==='share'?null:'share'))}
      </div>
    </div>}>
    <div className="safari-content" onKeyDown={event=>{if(event.key==='Escape')setPopover(null);}}>
      {sidebar && <aside className="safari-sidebar" aria-label="Safari sidebar">
        <h2>Safari</h2>
        <h3>Favorites</h3>
        {([['/','Research Work'],['/index','Index'],['/about','About Brian']] as [HubPath,string][]).map(([path,label])=><button type="button" key={path} disabled={!ready} aria-current={path===page.path?'page':undefined} onClick={()=>navigate(path)}><Icon name={path==='/'?'home':'book'}/>{label}</button>)}
        <h3>Reading List</h3>
        {saved.length ? saved.map(path=><button key={path} type="button" disabled={!ready} onClick={()=>navigate(path)}><Icon name="book"/>{path==='/'?'Research Work':path==='/about'?'About Brian':'Index'}</button>) : <p>Pages you save appear here.</p>}
        <small>Research gallery only</small>
      </aside>}
      <div className="safari-page-container">
        {origin && <iframe key={revision} ref={frame} src={frameSource} title="Research Work — Data Science Hub" inert={!!popover} aria-hidden={!!popover} sandbox="allow-scripts allow-same-origin allow-popups allow-popups-to-escape-sandbox" referrerPolicy="strict-origin-when-cross-origin"
          style={{width:`${100/zoom}%`,height:`${100/zoom}%`,transform:`scale(${zoom})`}}
          onLoad={()=>frame.current?.contentWindow?.postMessage({channel:HUB_CHANNEL,type:'hello'},origin)} />}
        {!ready && <div className="safari-loading" role="status"><span className="safari-site-mark">▥</span><strong>{failed?'Gallery connection unavailable':'Opening Research Work'}</strong><p>{failed?'The gallery bridge is not available yet. Your other desktop apps still work.':'Connecting to the research gallery…'}</p>{failed&&<button type="button" onClick={reload}>Try again</button>}</div>}
      </div>
    </div>
    {popover && <><button className="safari-popover-dismiss" aria-label="Dismiss Safari menu" onClick={()=>setPopover(null)}/><div className={`safari-popover safari-popover-${popover}`} role="dialog" aria-label={popover==='share'?'Share page':'Page options'}>
      {popover==='share'?<><strong>{page.title}</strong><button type="button" onClick={copyLink}>Copy Link</button><button type="button" onClick={()=>{setSaved(items=>items.includes(page.path)?items:[...items,page.path]);setNotice('Added to Reading List');setPopover(null);}}>Add to Reading List</button></>:<><strong>Page Zoom</strong><div className="safari-zoom"><button type="button" aria-label="Zoom out" disabled={zoom<=.8} onClick={()=>setZoom(value=>Math.max(.8,Math.round((value-.1)*10)/10))}>A−</button><button type="button" aria-label="Reset page zoom" onClick={()=>setZoom(1)}>{Math.round(zoom*100)}%</button><button type="button" aria-label="Zoom in" disabled={zoom>=1.5} onClick={()=>setZoom(value=>Math.min(1.5,Math.round((value+.1)*10)/10))}>A+</button></div></>}
    </div></>}
    {notice&&<div className="safari-notice" role="status">{notice}</div>}
  </DesktopWindow>;
}
