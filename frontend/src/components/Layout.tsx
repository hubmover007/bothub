import type { ReactNode } from 'react';

interface LayoutProps {
  children: ReactNode;
}

export default function Layout({ children }: LayoutProps) {
  return (
    <div className="min-h-screen bg-background">
      <header className="border-b">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <h1 className="text-2xl font-bold text-primary">🤖 BotHub</h1>
              <p className="text-sm text-muted-foreground">机器人管理平台</p>
            </div>
            <nav className="flex items-center space-x-4">
              <a href="/" className="text-sm font-medium hover:text-primary">大厅</a>
              <a href="/docs" className="text-sm font-medium hover:text-primary">文档</a>
            </nav>
          </div>
        </div>
      </header>
      <main className="container mx-auto px-4 py-8">
        {children}
      </main>
      <footer className="border-t mt-auto">
        <div className="container mx-auto px-4 py-6 text-center text-sm text-muted-foreground">
          © 2026 BotHub. 公司内部机器人管理平台.
        </div>
      </footer>
    </div>
  );
}
