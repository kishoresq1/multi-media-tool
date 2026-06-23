import { useEffect, useState } from 'react';
import { Player } from '@remotion/player';
import { Clapperboard, HardDrive } from 'lucide-react';
import { createAsset, uploadAssetVideo } from '../api/marketingApi.js';
import { IntelSummary } from './CampaignBuilder.jsx';
import { CyberVideoComposition } from './CyberVideoComposition.jsx';
import { ActionPanelSkeleton, GenerationSkeleton } from './LoadingSkeleton.jsx';
import { recordVideoFromScenes } from '../utils/videoCapture.js';

const VIDEO_TYPES = [
  { id: 'micro-visual', label: '5s Micro Visual', durationSeconds: 5 }
];

const STATUS = {
  idle: '',
  generating: 'Generating script…',
  recording: 'Recording video (plays in real time)…',
  uploading: 'Uploading to server…',
  done: null,   // filled dynamically with file path
  error: null
};

export default function VideoBuilder({ intel, onAssetCreated }) {
  const [asset, setAsset] = useState(null);
  const [videoType, setVideoType] = useState(VIDEO_TYPES[0]);
  const [loading, setLoading] = useState(false);
  const [saveStatus, setSaveStatus] = useState('');

  // Reset when intel changes — no auto-generate
  useEffect(() => {
    if (!intel) return;
    setAsset(null);
    setSaveStatus('');
  }, [intel?.id]);

  async function generate() {
    if (!intel || loading) return;
    setLoading(true);
    setSaveStatus(STATUS.generating);

    try {
      // 1. Generate script + store in DB
      const result = await createAsset(
        { ...intel, videoType: videoType.id, requestedDurationSeconds: videoType.durationSeconds },
        'video'
      );
      const newAsset = result.asset;
      setAsset(newAsset);
      onAssetCreated?.(newAsset);

      // 2. Capture real video from scenes
      setSaveStatus(STATUS.recording);
      let blob;
      try {
        blob = await recordVideoFromScenes(newAsset.content.scenes);
      } catch (err) {
        setSaveStatus(`Script saved. Video capture failed: ${err.message}`);
        setLoading(false);
        return;
      }

      // 3. Upload .webm to server
      setSaveStatus(STATUS.uploading);
      try {
        const uploaded = await uploadAssetVideo(newAsset.id, blob);
        setSaveStatus(`Saved → ${uploaded.filePath}`);
        // Update asset in parent gallery with the localFile path
        onAssetCreated?.({ ...newAsset, localFile: uploaded.filePath });
      } catch (err) {
        setSaveStatus(`Video recorded but upload failed: ${err.message}`);
      }
    } catch (err) {
      setSaveStatus(`Generation failed: ${err.message}`);
    } finally {
      setLoading(false);
    }
  }

  const script = asset?.content;
  const totalFrames = (script?.durationSeconds || 5) * 30;

  return (
    <section className="panel two-column">
      <div>
        <p className="eyebrow">Video Builder</p>
        <h2>5-Second Visual Preview</h2>
        <IntelSummary intel={intel} />
        <div className="segmented-control" aria-label="Video type">
          {VIDEO_TYPES.map((type) => (
            <button
              key={type.id}
              className={videoType.id === type.id ? 'active' : ''}
              onClick={() => setVideoType(type)}
              aria-pressed={videoType.id === type.id}
            >
              {type.label}
            </button>
          ))}
        </div>
        <button className="primary-action" onClick={generate} disabled={!intel || loading}>
          <Clapperboard size={16} />
          {loading ? saveStatus || 'Working…' : 'Generate 5s Visual'}
        </button>
        {!loading && saveStatus && (
          <div className="notice inline" style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            {saveStatus.startsWith('Saved') && <HardDrive size={13} />}
            {saveStatus}
          </div>
        )}
        {loading ? (
          <ActionPanelSkeleton rows={3} labelWidth={104} />
        ) : script && (
          <div className="scene-list">
            {script.scenes.map((scene) => (
              <div className="scene-card" key={scene.sceneNumber}>
                <strong>{scene.onScreenText}</strong>
                <span>{scene.narration}</span>
              </div>
            ))}
          </div>
        )}
      </div>
      <div className="preview-pane">
        {loading && !script ? (
          <GenerationSkeleton type="video" />
        ) : script ? (
          <Player
            component={CyberVideoComposition}
            inputProps={{ scenes: script.scenes }}
            durationInFrames={totalFrames}
            fps={30}
            compositionWidth={1280}
            compositionHeight={720}
            style={{ width: '100%', borderRadius: 8, overflow: 'hidden' }}
            acknowledgeRemotionLicense
            controls
          />
        ) : (
          <div className="empty-state">Select intel and click Generate 5s visual.</div>
        )}
      </div>
    </section>
  );
}
