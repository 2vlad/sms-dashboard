import { useState, useCallback, useMemo } from 'react';

interface UsePaginationOptions {
  initialPage?: number;
  initialPageSize?: number;
  totalItems: number;
}

interface UsePaginationReturn {
  page: number;
  pageSize: number;
  totalPages: number;
  startIndex: number;
  endIndex: number;
  hasNextPage: boolean;
  hasPreviousPage: boolean;
  setPage: (page: number) => void;
  setPageSize: (pageSize: number) => void;
  nextPage: () => void;
  previousPage: () => void;
  firstPage: () => void;
  lastPage: () => void;
  pageItems: (items: any[]) => any[];
}

function usePagination({
  initialPage = 1,
  initialPageSize = 10,
  totalItems,
}: UsePaginationOptions): UsePaginationReturn {
  const [page, setPage] = useState(initialPage);
  const [pageSize, setPageSize] = useState(initialPageSize);

  // Calculate total pages
  const totalPages = useMemo(() => Math.max(1, Math.ceil(totalItems / pageSize)), [totalItems, pageSize]);

  // Ensure current page is within bounds when total pages changes
  useMemo(() => {
    if (page > totalPages) {
      setPage(totalPages);
    }
  }, [totalPages, page]);

  // Calculate start and end indices
  const startIndex = useMemo(() => (page - 1) * pageSize, [page, pageSize]);
  const endIndex = useMemo(() => Math.min(startIndex + pageSize - 1, totalItems - 1), [startIndex, pageSize, totalItems]);

  // Navigation methods
  const nextPage = useCallback(() => {
    if (page < totalPages) {
      setPage(page + 1);
    }
  }, [page, totalPages]);

  const previousPage = useCallback(() => {
    if (page > 1) {
      setPage(page - 1);
    }
  }, [page]);

  const firstPage = useCallback(() => {
    setPage(1);
  }, []);

  const lastPage = useCallback(() => {
    setPage(totalPages);
  }, [totalPages]);

  // Get items for current page
  const pageItems = useCallback(
    (items: any[]) => {
      return items.slice(startIndex, endIndex + 1);
    },
    [startIndex, endIndex]
  );

  // Handle page size change
  const handlePageSizeChange = useCallback(
    (newPageSize: number) => {
      const newTotalPages = Math.max(1, Math.ceil(totalItems / newPageSize));
      const currentItem = (page - 1) * pageSize;
      const newPage = Math.min(Math.floor(currentItem / newPageSize) + 1, newTotalPages);
      
      setPageSize(newPageSize);
      setPage(newPage);
    },
    [page, pageSize, totalItems]
  );

  return {
    page,
    pageSize,
    totalPages,
    startIndex,
    endIndex,
    hasNextPage: page < totalPages,
    hasPreviousPage: page > 1,
    setPage,
    setPageSize: handlePageSizeChange,
    nextPage,
    previousPage,
    firstPage,
    lastPage,
    pageItems,
  };
}

export default usePagination; 