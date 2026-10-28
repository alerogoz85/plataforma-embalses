import type { Metadata } from "next";

// Una pantalla de administración no debe aparecer en buscadores.
export const metadata: Metadata = { title: "Actualizar los tableros", robots: { index: false, follow: false } };

export default function Layout({ children }: { children: React.ReactNode }) {
  return children;
}
