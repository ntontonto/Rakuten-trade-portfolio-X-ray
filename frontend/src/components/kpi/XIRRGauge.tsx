interface XIRRGaugeProps {
  xirr: number;
}

export default function XIRRGauge({ xirr }: XIRRGaugeProps) {
  const percentage = (xirr * 100).toFixed(2);
  const isPositive = xirr >= 0;

  return (
    <div className="flex flex-col items-center justify-center h-full">
      <div
        className={`text-6xl font-extrabold ${
          isPositive
            ? 'bg-gradient-to-r from-blue-600 to-cyan-500'
            : 'bg-gradient-to-r from-red-600 to-orange-500'
        } bg-clip-text text-transparent`}
      >
        {percentage}%
      </div>
      <p className="text-xs text-slate-400 font-medium mt-2">
        内部収益率 (年率)
      </p>
    </div>
  );
}
