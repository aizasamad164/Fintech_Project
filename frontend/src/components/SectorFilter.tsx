interface Props {
  sectors: string[];
  selected: string[];
  onChange: (selected: string[]) => void;
}

// FR-1.4: filter by individual sector(s) or a Combined Multi-Sector view.
export default function SectorFilter({ sectors, selected, onChange }: Props) {
  function toggle(sector: string) {
    if (selected.includes(sector)) {
      onChange(selected.filter((s) => s !== sector));
    } else {
      onChange([...selected, sector]);
    }
  }

  return (
    <div className="flex flex-wrap gap-2">
      {sectors.map((sector) => (
        <button
          key={sector}
          onClick={() => toggle(sector)}
          className={`px-3 py-1 rounded-full text-sm capitalize ${
            selected.includes(sector) ? 'bg-emerald-600 text-white' : 'bg-gray-100'
          }`}
        >
          {sector}
        </button>
      ))}
    </div>
  );
}
