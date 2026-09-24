import type { Metadata } from "next";
import { Geist_Mono, Montserrat, Nunito_Sans } from "next/font/google";
import "./globals.css";

// Tipografia institucional: Nunito Sans (texto) y Montserrat (titulos).
const nunito = Nunito_Sans({
  variable: "--font-nunito",
  subsets: ["latin"],
});

const montserrat = Montserrat({
  variable: "--font-montserrat",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Monitoreo de Embalses",
  description: "Plataforma empresarial de monitoreo y predicción de embalses e hidrología",
};

const SCRIPT_TEMA = `
(function () {
  try {
    var guardado = window.localStorage.getItem("tema");
    var oscuro = guardado ? guardado === "dark" : window.matchMedia("(prefers-color-scheme: dark)").matches;
    if (oscuro) document.documentElement.classList.add("dark");
  } catch (e) {}
})();
`;

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html
      lang="es"
      className={`${nunito.variable} ${montserrat.variable} ${geistMono.variable} h-full antialiased`}
      suppressHydrationWarning
    >
      <head>
        <script dangerouslySetInnerHTML={{ __html: SCRIPT_TEMA }} />
      </head>
      <body className="min-h-full flex flex-col bg-background text-foreground">{children}</body>
    </html>
  );
}
