import { useEffect, useRef, useState } from 'react';
import { Download, Image, Save } from 'lucide-react';
import { createAsset, uploadAssetImage } from '../api/marketingApi.js';
import { IntelSummary } from './CampaignBuilder.jsx';
import { GenerationSkeleton } from './LoadingSkeleton.jsx';
import TemplateRenderer from './templates/TemplateRenderer.jsx';

const TEMPLATE_TYPES = ['THREAT', 'COMPLIANCE', 'VULNERABILITY', 'BREACH', 'MISINFORMATION', 'DIGEST'];

export default function HyperFrameStudio({ intel, onAssetCreated }) {
  const [templateType, setTemplateType] = useState(intel?.classification || 'THREAT');
  const [asset, setAsset] = useState(null);
  const [saveStatus, setSaveStatus] = useState('');
  const [loading, setLoading] = useState(false);
  const canvasRef = useRef(null);

  useEffect(() => {
    if (!intel) return;
    setTemplateType(intel.classification || 'THREAT');
    setAsset(null);
    setSaveStatus('');
  }, [intel?.id]);

  async function generate(nextType = templateType) {
    if (!intel) return;
    setLoading(true);
    setSaveStatus('');
    try {
      const result = await createAsset({ ...intel, classification: nextType }, 'hyperframe');
      const newAsset = result.asset;
      setAsset(newAsset);
      onAssetCreated?.(newAsset);
      setSaveStatus('Asset saved to gallery.');

      setTimeout(async () => {
        try {
          const png = await captureCanvasPng(canvasRef.current);
          if (png) {
            await uploadAssetImage(newAsset.id, png);
            setSaveStatus('Image saved to disk.');
          }
        } catch {
          // PNG upload is best-effort because asset creation already succeeded.
        }
      }, 200);
    } finally {
      setLoading(false);
    }
  }

  async function downloadPng() {
    if (!canvasRef.current) return;
    setSaveStatus('Preparing PNG download.');
    const png = await captureCanvasPng(canvasRef.current);
    if (!png) return;
    const link = document.createElement('a');
    link.download = `sq1-${templateType.toLowerCase()}-${Date.now()}.png`;
    link.href = png;
    link.click();
    setSaveStatus('PNG download prepared.');
  }

  return (
    <section className="panel">
      <div className="panel-heading">
        <div>
          <p className="eyebrow">HyperFrame Studio</p>
          <h2>Visual Asset Generator</h2>
        </div>
        <button className="primary-action" onClick={() => generate()} disabled={!intel || loading}>
          <Image size={16} />
          {loading ? 'Generating content' : 'Generate content'}
        </button>
      </div>
      <div className="two-column">
        <div>
          <IntelSummary intel={intel} />
          <div className="template-grid">
            {TEMPLATE_TYPES.map((type) => (
              <button
                className={templateType === type ? 'template-button active' : 'template-button'}
                key={type}
                onClick={() => setTemplateType(type)}
                aria-pressed={templateType === type}
              >
                <span className={`swatch ${type.toLowerCase()}`} />
                {type}
              </button>
            ))}
          </div>
          <div className="action-row compact">
            <button onClick={downloadPng} disabled={!asset}>
              <Download size={15} />
              Download PNG
            </button>
            <button
              disabled={!asset}
              onClick={() => {
                onAssetCreated?.(asset);
                setSaveStatus('Saved to gallery.');
              }}
            >
              <Save size={15} />
              Save to Gallery
            </button>
          </div>
          {saveStatus && <div className="notice inline" role="status">{saveStatus}</div>}
        </div>
        <div className="visual-preview" ref={canvasRef}>
          {loading ? (
            <GenerationSkeleton type="visual" />
          ) : asset ? (
            <TemplateRenderer data={asset.content} type={templateType} />
          ) : (
            <div className="empty-state">Select intel and click Generate content.</div>
          )}
        </div>
      </div>
    </section>
  );
}

async function captureCanvasPng(el) {
  if (!el) return null;
  try {
    const { default: html2canvas } = await import('html2canvas');
    const canvas = await html2canvas(el, { scale: 1, useCORS: true });
    return canvas.toDataURL('image/png');
  } catch {
    return null;
  }
}
