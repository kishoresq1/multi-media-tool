import { AbsoluteFill, interpolate, Sequence, useCurrentFrame } from 'remotion';

function SceneView({ scene, startFrame }) {
  const frame = useCurrentFrame();
  const opacity = interpolate(frame - startFrame, [0, 10], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp'
  });
  const styles = {
    dark_grid: { background: 'oklch(0.965 0.008 83)' },
    red_pulse: { background: 'oklch(0.955 0.028 24)' },
    blue_wave: { background: 'oklch(0.94 0.025 238)' },
    amber_static: { background: 'oklch(0.965 0.035 58)' },
    matrix_rain: { background: 'oklch(0.955 0.032 155)' }
  };
  return (
    <AbsoluteFill
      style={{
        ...(styles[scene.bgStyle] || styles.dark_grid),
        opacity,
        color: 'oklch(0.22 0.026 248)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        flexDirection: 'column',
        padding: 80,
        fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", system-ui, sans-serif'
      }}
    >
      <p style={{ color: 'oklch(0.46 0.11 238)', fontSize: 26, margin: 0 }}>SQ1 SECURITY INTELLIGENCE</p>
      <h1 style={{ fontSize: 78, textAlign: 'center', lineHeight: 1.05 }}>{scene.onScreenText}</h1>
      <p style={{ color: 'oklch(0.38 0.028 248)', fontSize: 30, textAlign: 'center', maxWidth: 900 }}>
        {scene.narration}
      </p>
    </AbsoluteFill>
  );
}

export function CyberVideoComposition({ scenes = [] }) {
  let offset = 0;
  return (
    <AbsoluteFill style={{ background: 'oklch(0.965 0.008 83)' }}>
      {scenes.map((scene) => {
        const duration = scene.durationSeconds * 30;
        const currentOffset = offset;
        offset += duration;
        return (
          <Sequence key={scene.sceneNumber} from={currentOffset} durationInFrames={duration}>
            <SceneView scene={scene} startFrame={currentOffset} />
          </Sequence>
        );
      })}
    </AbsoluteFill>
  );
}
