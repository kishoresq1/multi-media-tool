import BaseTemplate from './BaseTemplate.jsx';

export default function ThreatTemplate({ data }) {
  return (
    <BaseTemplate
      data={data}
      accentColor="var(--accent-red)"
      background="oklch(0.955 0.028 24)"
      label="THREAT ALERT"
    />
  );
}
