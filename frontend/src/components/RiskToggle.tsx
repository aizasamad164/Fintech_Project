type RiskStrategy = 'conservative' | 'balanced' | 'aggressive';

interface Props {
  value: RiskStrategy;
  onChange: (value: RiskStrategy) => void;
}

const OPTIONS: RiskStrategy[] = ['conservative', 'balanced', 'aggressive'];

// FR-1.3: three selectable risk strategies.
// FR-6.2: updates trigger regeneration without a full page reload.
export default function RiskToggle({ value, onChange }: Props) {
  return (
    <div className="flex gap-2">
      {OPTIONS.map((option) => (
        <button
          key={option}
          onClick={() => onChange(option)}
          className={`px-4 py-2 rounded-full capitalize ${
            value === option ? 'bg-indigo-600 text-white' : 'bg-gray-100'
          }`}
        >
          {option}
        </button>
      ))}
    </div>
  );
}
