import { Link } from 'react-router-dom';
import type { Bot } from '../types/bot';

interface BotCardProps {
  bot: Bot;
}

export default function BotCard({ bot }: BotCardProps) {
  return (
    <Link to={`/bots/${bot.bot_id}`} className="block">
      <div className="border rounded-lg p-6 hover:shadow-lg transition-shadow cursor-pointer">
        <div className="flex items-start justify-between mb-4">
          <div className="flex-1">
            <h3 className="text-lg font-semibold mb-1">{bot.bot_name}</h3>
            <p className="text-sm text-muted-foreground">{bot.bot_id}</p>
          </div>
          <div className={`w-3 h-3 rounded-full ${
            bot.status === 'online' ? 'bg-green-500' :
            bot.status === 'offline' ? 'bg-gray-400' :
            'bg-red-500'
          }`} />
        </div>

        <p className="text-sm text-muted-foreground mb-4 line-clamp-2">
          {bot.description || '无描述'}
        </p>

        <div className="flex flex-wrap gap-2">
          {bot.capabilities.slice(0, 3).map((cap) => (
            <span key={cap} className="px-2 py-1 bg-secondary text-secondary-foreground rounded text-xs">
              {cap}
            </span>
          ))}
          {bot.capabilities.length > 3 && (
            <span className="px-2 py-1 bg-secondary text-secondary-foreground rounded text-xs">
              +{bot.capabilities.length - 3}
            </span>
          )}
        </div>

        <div className="mt-4 pt-4 border-t text-xs text-muted-foreground">
          创建于 {new Date(bot.created_at).toLocaleDateString('zh-CN')}
        </div>
      </div>
    </Link>
  );
}
