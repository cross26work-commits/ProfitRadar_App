type Column = {
  key: string;
  label: string;
};

type TableProps = {
  columns: Column[];
  rows: Record<string, string | number>[];
};

export function Table({ columns, rows }: TableProps) {
  return (
    <div className="overflow-hidden rounded-2xl border border-slate-200 bg-white">
      <table className="w-full text-left text-sm">
        <thead className="bg-slate-50 text-slate-500">
          <tr>
            {columns.map((column) => (
              <th key={column.key} className="px-4 py-3 font-bold">
                {column.label}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100">
          {rows.map((row, index) => (
            <tr key={index} className="text-slate-700">
              {columns.map((column) => (
                <td key={column.key} className="px-4 py-4 font-medium">
                  {row[column.key]}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
