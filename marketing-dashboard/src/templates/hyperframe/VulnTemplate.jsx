import BaseTemplate from './BaseTemplate.jsx';

export default function VulnTemplate({ data }) {
  return (
    <BaseTemplate
      data={data}
      accentColor="var(--accent-yellow)"
      background="oklch(0.965 0.035 82)"
      label="VULNERABILITY"
    />
  );
}
