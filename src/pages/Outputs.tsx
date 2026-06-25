import { useState } from 'react';
import { FileText, Image, FileCode, File, ExternalLink, FolderOpen } from 'lucide-react';
import { PageWrapper } from '@/components/layout/PageWrapper';
import { Card } from '@/components/ui/card';
import { ScrollArea } from '@/components/ui/scroll-area';
import { MarkdownRenderer } from '@/components/chat/MarkdownRenderer';
import { useOutputs } from '@/hooks/useOutputs';
import type { Output } from '@/types';

const typeIcons: Record<Output['type'], React.ElementType> = {
  markdown: FileText,
  html: FileCode,
  image: Image,
  pdf: File,
  link: ExternalLink,
};

export default function Outputs() {
  const { data: outputs = [], isLoading } = useOutputs();
  const [selectedId, setSelectedId] = useState<string | null>(outputs[0]?.id || null);

  const selectedOutput = outputs.find((o) => o.id === selectedId) || outputs[0];

  return (
    <PageWrapper className="flex h-[calc(100vh-8rem)] gap-4">
      {/* 左侧目录树 */}
      <Card className="flex w-72 flex-col overflow-hidden">
        <div className="border-b p-4">
          <h2 className="font-semibold">成果目录</h2>
        </div>
        <ScrollArea className="flex-1 p-2">
          {isLoading ? (
            <div className="space-y-2">
              {[1, 2, 3, 4].map((i) => (
                <div key={i} className="h-10 animate-pulse rounded-lg bg-muted" />
              ))}
            </div>
          ) : (
            <div className="space-y-1">
              {outputs.map((output) => {
                const Icon = typeIcons[output.type];
                return (
                  <button
                    key={output.id}
                    onClick={() => setSelectedId(output.id)}
                    className={`flex w-full items-center gap-2 rounded-lg px-3 py-2 text-left text-sm transition-colors ${
                      selectedOutput?.id === output.id
                        ? 'bg-primary/10 text-primary'
                        : 'text-muted-foreground hover:bg-accent hover:text-accent-foreground'
                    }`}
                  >
                    <Icon className="h-4 w-4 shrink-0" />
                    <span className="truncate">{output.name}</span>
                  </button>
                );
              })}
            </div>
          )}
        </ScrollArea>
      </Card>

      {/* 右侧预览区 */}
      <Card className="flex flex-1 flex-col overflow-hidden">
        {selectedOutput ? (
          <>
            <div className="flex items-center justify-between border-b px-5 py-3">
              <div className="flex items-center gap-2">
                {(() => {
                  const Icon = typeIcons[selectedOutput.type];
                  return <Icon className="h-5 w-5 text-primary" />;
                })()}
                <h3 className="font-semibold">{selectedOutput.name}</h3>
              </div>
              <span className="text-xs text-muted-foreground">
                来源：{selectedOutput.source === 'task' ? '任务' : selectedOutput.source === 'meeting' ? '会议' : '上传'} ·{' '}
                {new Date(selectedOutput.createdAt).toLocaleString('zh-CN')}
              </span>
            </div>
            <ScrollArea className="flex-1 p-6">
              <OutputPreview output={selectedOutput} />
            </ScrollArea>
          </>
        ) : (
          <div className="flex flex-1 flex-col items-center justify-center text-muted-foreground">
            <FolderOpen className="h-12 w-12 mb-3 opacity-30" />
            <p>选择一个文件进行预览</p>
          </div>
        )}
      </Card>
    </PageWrapper>
  );
}

function OutputPreview({ output }: { output: Output }) {
  switch (output.type) {
    case 'markdown':
      return <MarkdownRenderer content={output.content || ''} />;
    case 'html':
      return (
        <div
          className="prose prose-sm max-w-none"
          dangerouslySetInnerHTML={{ __html: output.content || '' }}
        />
      );
    case 'image':
      return (
        <div className="flex justify-center">
          <img
            src={output.url}
            alt={output.name}
            className="max-h-[600px] rounded-lg object-contain shadow-sm"
          />
        </div>
      );
    case 'pdf':
      return (
        <div className="flex flex-col items-center justify-center rounded-lg bg-secondary/50 p-12 text-center">
          <File className="h-16 w-16 text-muted-foreground" />
          <p className="mt-4 font-medium">{output.name}</p>
          <p className="text-sm text-muted-foreground">PDF 预览需要后端支持，当前为占位</p>
        </div>
      );
    case 'link':
      return (
        <div className="flex flex-col items-center justify-center rounded-lg bg-secondary/50 p-12 text-center">
          <ExternalLink className="h-12 w-12 text-primary" />
          <p className="mt-4 font-medium">{output.name}</p>
          <a
            href={output.url}
            target="_blank"
            rel="noreferrer"
            className="mt-2 text-primary hover:underline"
          >
            {output.url}
          </a>
        </div>
      );
    default:
      return <p className="text-muted-foreground">不支持的文件类型</p>;
  }
}
