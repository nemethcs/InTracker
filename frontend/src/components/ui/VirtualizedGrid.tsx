import { useRef, useMemo, useState, useEffect } from 'react'
import { useVirtualizer } from '@tanstack/react-virtual'
import { cn } from '@/lib/utils'

interface VirtualizedGridProps<T> {
  items: T[]
  renderItem: (item: T, index: number) => React.ReactNode
  columns?: number | ((width: number) => number)
  gap?: number
  className?: string
  containerClassName?: string
  itemHeight?: number
  overscan?: number
  estimateSize?: (index: number) => number
}

/**
 * Virtualized grid component for efficiently rendering large lists.
 * Only renders visible items, significantly improving performance for long lists.
 * 
 * @example
 * ```tsx
 * <VirtualizedGrid
 *   items={todos}
 *   columns={3}
 *   gap={16}
 *   renderItem={(todo) => <TodoCard todo={todo} />}
 * />
 * ```
 */
export function VirtualizedGrid<T>({
  items,
  renderItem,
  columns = 3,
  gap = 16,
  className,
  containerClassName,
  itemHeight = 200,
  overscan = 5,
  estimateSize,
}: VirtualizedGridProps<T>) {
  const parentRef = useRef<HTMLDivElement>(null)
  const [windowWidth, setWindowWidth] = useState(typeof window !== 'undefined' ? window.innerWidth : 1024)

  // Update window width on resize
  useEffect(() => {
    if (typeof window === 'undefined') return

    const handleResize = () => {
      setWindowWidth(window.innerWidth)
    }

    window.addEventListener('resize', handleResize)
    return () => window.removeEventListener('resize', handleResize)
  }, [])

  // Calculate columns based on window width or use static value
  const calculatedColumns = useMemo(() => {
    if (typeof columns === 'function') {
      return columns(windowWidth)
    }
    return columns
  }, [columns, windowWidth])

  // Calculate rows based on columns
  const rowCount = Math.ceil(items.length / calculatedColumns)

  // Create virtualizer for rows
  const rowVirtualizer = useVirtualizer({
    count: rowCount,
    getScrollElement: () => parentRef.current,
    estimateSize: estimateSize || (() => itemHeight + gap),
    overscan,
  })

  // Group items into rows
  const rows = useMemo(() => {
    const result: T[][] = []
    for (let i = 0; i < rowCount; i++) {
      const row: T[] = []
      for (let j = 0; j < calculatedColumns; j++) {
        const index = i * calculatedColumns + j
        if (index < items.length) {
          row.push(items[index])
        }
      }
      result.push(row)
    }
    return result
  }, [items, calculatedColumns, rowCount])

  return (
    <div
      ref={parentRef}
      className={cn('overflow-auto', containerClassName)}
      style={{ height: '100%', width: '100%' }}
    >
      <div
        className={cn('relative', className)}
        style={{
          height: `${rowVirtualizer.getTotalSize()}px`,
          width: '100%',
        }}
      >
        {rowVirtualizer.getVirtualItems().map((virtualRow) => {
          const row = rows[virtualRow.index]
          if (!row || row.length === 0) return null

          return (
            <div
              key={virtualRow.key}
              className="absolute top-0 left-0 w-full"
              style={{
                height: `${virtualRow.size}px`,
                transform: `translateY(${virtualRow.start}px)`,
              }}
            >
              <div
                className="grid w-full"
                style={{
                  gridTemplateColumns: `repeat(${calculatedColumns}, 1fr)`,
                  gap: `${gap}px`,
                }}
              >
                {row.map((item, colIndex) => {
                  const globalIndex = virtualRow.index * calculatedColumns + colIndex
                  return (
                    <div key={globalIndex}>
                      {renderItem(item, globalIndex)}
                    </div>
                  )
                })}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
