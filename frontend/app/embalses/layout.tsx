import type { Metadata } from "next";

// La pagina es de cliente y no puede exportar metadatos; el titulo de la pestana va aqui.
export const metadata: Metadata = { title: "Monitoreo de Embalses" };

export default function EmbalsesLayout({ children }: { children: React.ReactNode }) {
  return children;
}
