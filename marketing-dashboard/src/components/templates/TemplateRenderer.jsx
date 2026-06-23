import ThreatTemplate from '../../templates/hyperframe/ThreatTemplate.jsx';
import ComplianceTemplate from '../../templates/hyperframe/ComplianceTemplate.jsx';
import VulnTemplate from '../../templates/hyperframe/VulnTemplate.jsx';
import BreachTemplate from '../../templates/hyperframe/BreachTemplate.jsx';
import MisinfoTemplate from '../../templates/hyperframe/MisinfoTemplate.jsx';
import DigestTemplate from '../../templates/hyperframe/DigestTemplate.jsx';

const TEMPLATES = {
  THREAT: ThreatTemplate,
  COMPLIANCE: ComplianceTemplate,
  VULNERABILITY: VulnTemplate,
  BREACH: BreachTemplate,
  MISINFORMATION: MisinfoTemplate,
  DIGEST: DigestTemplate
};

export default function TemplateRenderer({ data, type = 'THREAT' }) {
  const Template = TEMPLATES[type] || ThreatTemplate;
  return <Template data={data} />;
}
