import BaseTemplate from './BaseTemplate.jsx';

export default function BreachTemplate({ data }) {
  return (
    <BaseTemplate
      data={data}
      accentColor="var(--accent-orange)"
      background="oklch(0.965 0.035 58)"
      label="BREACH ALERT"
    />
  );
}
