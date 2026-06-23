import { useState } from 'react'
import { Check, Link2, Image as ImageIcon, Video, Wand2, Sparkles, Settings2, Edit3, X, Save, Plus } from 'lucide-react'
import { PageHeader } from '../components/shared'

interface ToolConfig {
  id: string
  name: string
  description: string
  icon: any
  type: 'image' | 'video'
  envKeys: string[]
  status: 'connected' | 'optional' | 'planned'
  isCustom?: boolean
}

const INITIAL_IMAGE_TOOLS: ToolConfig[] = [
  {
    id: 'midjourney',
    name: 'Midjourney',
    description: 'High-quality artistic image generation. Requires Discord webhook or API bridge configuration.',
    icon: Wand2,
    type: 'image',
    envKeys: ['ZDR_MIDJOURNEY_API_KEY', 'ZDR_MIDJOURNEY_WEBHOOK'],
    status: 'optional',
  },
  {
    id: 'dalle',
    name: 'DALL-E 3',
    description: 'OpenAI\'s powerful image generation model. Integrated via OpenAI API.',
    icon: Sparkles,
    type: 'image',
    envKeys: ['OPENAI_API_KEY'],
    status: 'connected',
  },
  {
    id: 'stablediffusion',
    name: 'Stable Diffusion',
    description: 'Open-source image generation. Can be run locally or via Automatic1111/ComfyUI API.',
    icon: ImageIcon,
    type: 'image',
    envKeys: ['ZDR_SD_API_URL'],
    status: 'optional',
  },
]

const INITIAL_VIDEO_TOOLS: ToolConfig[] = [
  {
    id: 'runway',
    name: 'Runway Gen-2',
    description: 'Professional AI video generation and editing tools.',
    icon: Video,
    type: 'video',
    envKeys: ['ZDR_RUNWAY_API_KEY'],
    status: 'planned',
  },
  {
    id: 'pika',
    name: 'Pika Labs',
    description: 'Animation and video generation from text and images.',
    icon: Video,
    type: 'video',
    envKeys: ['ZDR_PIKA_API_KEY'],
    status: 'planned',
  },
  {
    id: 'sora',
    name: 'OpenAI Sora',
    description: 'Next-generation photorealistic video generation.',
    icon: Sparkles,
    type: 'video',
    envKeys: ['OPENAI_API_KEY'],
    status: 'planned',
  },
]

export function StudioConfig() {
  const [imageTools, setImageTools] = useState<ToolConfig[]>(INITIAL_IMAGE_TOOLS)
  const [videoTools, setVideoTools] = useState<ToolConfig[]>(INITIAL_VIDEO_TOOLS)
  const [connected, setConnected] = useState<Record<string, boolean>>({
    'dalle': true
  })
  const [activeImageTool, setActiveImageTool] = useState<string>('dalle')
  const [activeVideoTool, setActiveVideoTool] = useState<string>('')
  const [editingTool, setEditingTool] = useState<ToolConfig | null>(null)
  const [isAddingTool, setIsAddingTool] = useState<'image' | 'video' | null>(null)
  const [configValues, setConfigValues] = useState<Record<string, string>>({})
  
  // New tool form state
  const [newTool, setNewTool] = useState({
    name: '',
    description: '',
    envKeys: ''
  })

  const statusBadge = (tool: ToolConfig) => {
    const isActive = (tool.type === 'image' && activeImageTool === tool.id) || 
                     (tool.type === 'video' && activeVideoTool === tool.id)
    
    if (isActive) return <span className="badge badge-success">Active</span>
    if (connected[tool.id]) return <span className="badge badge-accent">Connected</span>
    if (tool.status === 'optional' || tool.isCustom) return <span className="badge badge-warning">Configure</span>
    return <span className="badge badge-neutral">Coming soon</span>
  }

  const handleToggleActive = (tool: ToolConfig) => {
    if (!connected[tool.id] && tool.status !== 'connected') {
      setEditingTool(tool)
      return
    }

    if (tool.type === 'image') {
      setActiveImageTool(activeImageTool === tool.id ? '' : tool.id)
    } else {
      setActiveVideoTool(activeVideoTool === tool.id ? '' : tool.id)
    }
  }

  const handleSaveConfig = () => {
    if (editingTool) {
      setConnected(prev => ({ ...prev, [editingTool.id]: true }))
      if (editingTool.type === 'image') setActiveImageTool(editingTool.id)
      else setActiveVideoTool(editingTool.id)
    }
    setEditingTool(null)
  }

  const handleAddCustomTool = () => {
    if (!newTool.name || !isAddingTool) return

    const toolId = newTool.name.toLowerCase().replace(/\s+/g, '-')
    const tool: ToolConfig = {
      id: toolId,
      name: newTool.name,
      description: newTool.description || `Custom ${isAddingTool} generation tool.`,
      icon: isAddingTool === 'image' ? ImageIcon : Video,
      type: isAddingTool,
      envKeys: newTool.envKeys.split(',').map(k => k.trim()).filter(Boolean),
      status: 'optional',
      isCustom: true
    }

    if (isAddingTool === 'image') {
      setImageTools(prev => [...prev, tool])
    } else {
      setVideoTools(prev => [...prev, tool])
    }

    setIsAddingTool(null)
    setNewTool({ name: '', description: '', envKeys: '' })
    setEditingTool(tool) // Open config immediately for the new tool
  }

  const renderToolCard = (tool: ToolConfig) => {
    const isActive = (tool.type === 'image' && activeImageTool === tool.id) || 
                     (tool.type === 'video' && activeVideoTool === tool.id)
    const isConnected = connected[tool.id] || tool.status === 'connected'

    return (
      <article key={tool.id} className={`integration-card ${isActive ? 'active' : ''}`} style={isActive ? { borderColor: 'var(--accent)', boxShadow: '0 0 0 2px var(--accent-glow)' } : {}}>
        <div className="integration-card-header">
          <div className="integration-icon" style={{ background: 'var(--bg-subtle)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <tool.icon size={20} />
          </div>
          <div style={{ flex: 1 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <h4>{tool.name}</h4>
              {statusBadge(tool)}
            </div>
          </div>
        </div>
        <p>{tool.description}</p>
        
        <div style={{ marginTop: 'auto', paddingTop: '1rem', display: 'flex', gap: '0.5rem' }}>
          {tool.status !== 'planned' || tool.isCustom ? (
            <>
              <button
                type="button"
                className={`btn ${isActive ? 'btn-primary' : 'btn-secondary'}`}
                style={{ flex: 2 }}
                onClick={() => handleToggleActive(tool)}
              >
                {isActive ? <Check size={14} /> : (isConnected ? <Link2 size={14} /> : <Settings2 size={14} />)}
                {isActive ? 'Active' : (isConnected ? 'Set Active' : 'Configure')}
              </button>
              <button
                type="button"
                className="btn btn-secondary"
                style={{ padding: '0.5rem' }}
                onClick={() => setEditingTool(tool)}
                title="Edit Configuration"
              >
                <Edit3 size={14} />
              </button>
            </>
          ) : (
            <button type="button" className="btn btn-secondary" style={{ flex: 1 }} disabled>
              Coming Soon
            </button>
          )}
        </div>
      </article>
    )
  }

  return (
    <>
      <PageHeader 
        title="Studio Configuration" 
        description="Configure AI tools for automated content generation. Select which tools are active for image and video tasks."
      />

      <section style={{ marginTop: '2rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem' }}>
          <ImageIcon size={20} className="text-primary" />
          <h3 style={{ margin: 0 }}>Image Generation</h3>
          <button 
            className="btn btn-secondary btn-sm" 
            style={{ marginLeft: '1rem' }}
            onClick={() => setIsAddingTool('image')}
          >
            <Plus size={14} /> Add Tool
          </button>
          <span style={{ marginLeft: 'auto', fontSize: '0.8rem', color: 'var(--text-muted)' }}>
            {activeImageTool ? `Active: ${imageTools.find(t => t.id === activeImageTool)?.name}` : 'No tool active'}
          </span>
        </div>
        <div className="integration-grid">
          {imageTools.map(renderToolCard)}
        </div>
      </section>

      <section style={{ marginTop: '3rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem' }}>
          <Video size={20} className="text-primary" />
          <h3 style={{ margin: 0 }}>Video Generation</h3>
          <button 
            className="btn btn-secondary btn-sm" 
            style={{ marginLeft: '1rem' }}
            onClick={() => setIsAddingTool('video')}
          >
            <Plus size={14} /> Add Tool
          </button>
          <span style={{ marginLeft: 'auto', fontSize: '0.8rem', color: 'var(--text-muted)' }}>
            {activeVideoTool ? `Active: ${videoTools.find(t => t.id === activeVideoTool)?.name}` : 'No tool active'}
          </span>
        </div>
        <div className="integration-grid">
          {videoTools.map(renderToolCard)}
        </div>
      </section>

      <section className="config-section" style={{ marginTop: '3rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1.5rem', paddingBottom: '0.75rem', borderBottom: '1px solid var(--border)' }}>
          <Settings2 size={20} />
          <h3 style={{ margin: 0 }}>Global Studio Settings</h3>
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '1.5rem' }}>
          <div className="form-group">
            <label>Default Image Aspect Ratio</label>
            <select>
              <option>16:9 (Widescreen)</option>
              <option>1:1 (Square)</option>
              <option>4:5 (Portrait)</option>
              <option>9:16 (Story)</option>
            </select>
          </div>
          <div className="form-group">
            <label>Content Safety Filter</label>
            <select>
              <option>Strict</option>
              <option>Moderate</option>
              <option>None</option>
            </select>
          </div>
          <div className="form-group">
            <label>Auto-generate Assets</label>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginTop: '0.75rem' }}>
              <input type="checkbox" id="auto-gen" defaultChecked style={{ width: 'auto' }} />
              <label htmlFor="auto-gen" style={{ margin: 0, fontWeight: 400 }}>Generate images for high-score posts</label>
            </div>
          </div>
        </div>
      </section>

      {/* Configuration Modal */}
      {editingTool && (
        <div className="modal-overlay" onClick={() => setEditingTool(null)}>
          <div className="modal-card" onClick={e => e.stopPropagation()}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                <div className="integration-icon" style={{ width: 40, height: 40, background: 'var(--bg-subtle)' }}>
                  <editingTool.icon size={20} />
                </div>
                <div>
                  <h3 style={{ margin: 0 }}>Configure {editingTool.name}</h3>
                  <p style={{ margin: 0, fontSize: '0.85rem', color: 'var(--text-muted)' }}>{editingTool.type === 'image' ? 'Image' : 'Video'} Generation Tool</p>
                </div>
              </div>
              <button className="btn-ghost" onClick={() => setEditingTool(null)}><X size={20} /></button>
            </div>

            <div style={{ marginBottom: '1.5rem' }}>
              <p style={{ fontSize: '0.9rem', color: 'var(--text-muted)', marginBottom: '1.5rem' }}>
                Enter the required credentials to enable this tool. These values are stored securely in the backend environment.
              </p>
              
              {editingTool.envKeys.length > 0 ? editingTool.envKeys.map(key => (
                <div key={key} className="form-group">
                  <label>{key.replace('ZDR_', '').replace(/_/g, ' ')}</label>
                  <input 
                    type="password" 
                    placeholder={`Enter ${key}...`}
                    value={configValues[key] || ''}
                    onChange={e => setConfigValues(prev => ({ ...prev, [key]: e.target.value }))}
                  />
                </div>
              )) : (
                <p style={{ textAlign: 'center', padding: '1rem', background: 'var(--bg)', borderRadius: 8, border: '1px dashed var(--border)' }}>
                  No environment keys required for this tool.
                </p>
              )}
            </div>

            <div className="modal-actions">
              <button className="btn btn-secondary" onClick={() => setEditingTool(null)}>Cancel</button>
              <button className="btn btn-primary" onClick={handleSaveConfig}>
                <Save size={14} />
                Save Configuration
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Add Tool Modal */}
      {isAddingTool && (
        <div className="modal-overlay" onClick={() => setIsAddingTool(null)}>
          <div className="modal-card" onClick={e => e.stopPropagation()}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
              <h3 style={{ margin: 0 }}>Add New {isAddingTool === 'image' ? 'Image' : 'Video'} Tool</h3>
              <button className="btn-ghost" onClick={() => setIsAddingTool(null)}><X size={20} /></button>
            </div>

            <div className="form-group">
              <label>Tool Name</label>
              <input 
                type="text" 
                placeholder="e.g. My Custom Generator"
                value={newTool.name}
                onChange={e => setNewTool(prev => ({ ...prev, name: e.target.value }))}
              />
            </div>

            <div className="form-group">
              <label>Description</label>
              <textarea 
                placeholder="What does this tool do?"
                rows={3}
                value={newTool.description}
                onChange={e => setNewTool(prev => ({ ...prev, description: e.target.value }))}
              />
            </div>

            <div className="form-group">
              <label>Required Env Keys (comma separated)</label>
              <input 
                type="text" 
                placeholder="e.g. API_KEY, ENDPOINT_URL"
                value={newTool.envKeys}
                onChange={e => setNewTool(prev => ({ ...prev, envKeys: e.target.value }))}
              />
              <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.5rem' }}>
                These keys will be requested during tool configuration.
              </p>
            </div>

            <div className="modal-actions">
              <button className="btn btn-secondary" onClick={() => setIsAddingTool(null)}>Cancel</button>
              <button className="btn btn-primary" onClick={handleAddCustomTool} disabled={!newTool.name}>
                <Plus size={14} />
                Add Tool
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  )
}
