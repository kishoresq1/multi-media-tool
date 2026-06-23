import BaseTemplate from './BaseTemplate.jsx';

export default function MisinfoTemplate({ data }) {
  return (
    <BaseTemplate
      data={data}
      accentColor="var(--accent-green)"
      background="oklch(0.955 0.032 155)"
      label="MISINFO CHECK"
    />
  );
}
