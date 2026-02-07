export default function NotFound() {
  return (
    <div className="text-center py-24">
      <h1 className="text-6xl font-bold text-muted-foreground mb-4">404</h1>
      <p className="text-xl text-muted-foreground mb-8">页面不存在</p>
      <a href="/" className="px-6 py-3 bg-primary text-primary-foreground rounded-md hover:bg-primary/90">
        返回首页
      </a>
    </div>
  );
}
