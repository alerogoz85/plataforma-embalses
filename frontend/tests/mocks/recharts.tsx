import type { ReactNode } from "react";

/**
 * jsdom no calcula tamanos, asi que Recharts no dibuja. Estos dobles exponen
 * como atributos data-* lo que cada componente de grafico recibio, para poder
 * verificar los datos y la configuracion que nuestro codigo le entrega.
 */
type Props = Record<string, unknown> & { children?: ReactNode };

export const ResponsiveContainer = ({ children }: Props) => <div>{children}</div>;

function contenedor(nombre: string) {
  return function Grafico({ data, children }: Props) {
    return (
      <div data-testid={nombre} data-points={JSON.stringify(data)}>
        {children}
      </div>
    );
  };
}

export const ComposedChart = contenedor("composed-chart");
export const BarChart = contenedor("bar-chart");

export const Line = ({ dataKey, name, strokeDasharray }: Props) => (
  <div data-testid="line" data-key={String(dataKey)} data-name={String(name)} data-dashed={String(Boolean(strokeDasharray))} />
);

export const Area = ({ dataKey, name, stackId }: Props) => (
  <div data-testid="area" data-key={String(dataKey)} data-name={String(name ?? "")} data-stack={String(stackId ?? "")} />
);

export const Bar = ({ dataKey, children }: Props) => (
  <div data-testid="bar" data-key={String(dataKey)}>
    {children}
  </div>
);

export const Cell = ({ fill }: Props) => <div data-testid="cell" data-fill={String(fill)} />;

export const YAxis = ({ domain, dataKey }: Props) => {
  const limite = Array.isArray(domain) ? domain[1] : undefined;
  const evaluar = (valor: number) => (typeof limite === "function" ? limite(valor) : limite);
  return (
    <div
      data-testid="y-axis"
      data-key={String(dataKey ?? "")}
      data-max-bajo={String(evaluar(80))}
      data-max-alto={String(evaluar(130.2))}
    />
  );
};

export const XAxis = ({ domain, dataKey }: Props) => {
  const limite = Array.isArray(domain) ? domain[1] : undefined;
  const evaluar = (valor: number) => (typeof limite === "function" ? limite(valor) : limite);
  return (
    <div
      data-testid="x-axis"
      data-key={String(dataKey ?? "")}
      data-max-bajo={String(evaluar(80))}
      data-max-alto={String(evaluar(130.2))}
    />
  );
};

const Nada = () => null;
export const CartesianGrid = Nada;
export const Tooltip = Nada;
export const Legend = Nada;
