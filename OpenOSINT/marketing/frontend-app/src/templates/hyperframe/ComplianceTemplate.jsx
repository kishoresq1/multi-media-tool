import BaseTemplate from './BaseTemplate.jsx';

export default function ComplianceTemplate({ data }) {
  return (
    <BaseTemplate
      data={data}
      accentColor="var(--accent-blue)"
      background="oklch(0.94 0.025 238)"
      label="COMPLIANCE UPDATE"
    />
  );
}
