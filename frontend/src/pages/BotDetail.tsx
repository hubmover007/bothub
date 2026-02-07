import { useParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import apiClient from '../api/client';
import type { Bot } from '../types/bot';

export default function BotDetail() {
  const { botId } = useParams<{ botId: string }>();

  const { data: bot, isLoading, error } = useQuery({
    queryKey: ['bot', botId],
    queryFn: async () => {
      const response = await apiClient.get<Bot>(`/api/v1/bots/${botId}`);
      return response.data;
    },
    enabled: !!botId,
  });

  if (isLoading) {
    return <div className="text-center py-12">加载中...</div>;
  }

  if (error || !bot) {
    return <div className="text-center py-12 text-destructive">机器人不存在</div>;
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-3xl font-bold">{bot.bot_name}</h1>
          <p className="text-muted-foreground">{bot.bot_id}</p>
        </div>
        <div className={`px-3 py-1 rounded-full text-sm font-medium ${
          bot.status === 'online' ? 'bg-green-100 text-green-800' :
          bot.status === 'offline' ? 'bg-gray-100 text-gray-800' :
          'bg-red-100 text-red-800'
        }`}>
          {bot.status === 'online' ? '在线' : bot.status === 'offline' ? '离线' : '错误'}
        </div>
      </div>

      <div className="border rounded-lg p-6 space-y-4">
        <div>
          <h2 className="font-semibold mb-2">描述</h2>
          <p className="text-muted-foreground">{bot.description || '无描述'}</p>
        </div>

        <div>
          <h2 className="font-semibold mb-2">能力</h2>
          <div className="flex flex-wrap gap-2">
            {bot.capabilities.map((cap) => (
              <span key={cap} className="px-2 py-1 bg-secondary text-secondary-foreground rounded text-sm">
                {cap}
              </span>
            ))}
          </div>
        </div>

        {bot.endpoint && (
          <div>
            <h2 className="font-semibold mb-2">API 端点</h2>
            <code className="block p-2 bg-secondary rounded text-sm">{bot.endpoint}</code>
          </div>
        )}

        <div className="grid grid-cols-2 gap-4 pt-4 border-t">
          <div>
            <p className="text-sm text-muted-foreground">版本</p>
            <p className="font-medium">{bot.version || 'N/A'}</p>
          </div>
          <div>
            <p className="text-sm text-muted-foreground">创建时间</p>
            <p className="font-medium">{new Date(bot.created_at).toLocaleString('zh-CN')}</p>
          </div>
          {bot.last_heartbeat_at && (
            <div>
              <p className="text-sm text-muted-foreground">最后心跳</p>
              <p className="font-medium">{new Date(bot.last_heartbeat_at).toLocaleString('zh-CN')}</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
