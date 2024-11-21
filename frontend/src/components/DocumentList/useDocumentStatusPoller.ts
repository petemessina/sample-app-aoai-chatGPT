import { useState, useEffect } from 'react';
import { getDocumentStatuses, UploadedDocument } from '../../api';

const useDocumentStatusPoller = (pendingDocuments: Array<UploadedDocument>, interval: number) => {
  const [documentStatuses, setDocumentStatuses] = useState<Array<UploadedDocument>>([]);

  useEffect(() => {
    let isMounted = true;

    const fetchData = async () => {
      if (pendingDocuments && pendingDocuments.length > 0) {
        const documentStatuses = await getDocumentStatuses(pendingDocuments.map((doc) => doc.id)) ?? [];
        if (isMounted) {
          setDocumentStatuses(documentStatuses);
        }
      }
    };

    fetchData();
    const intervalId = setInterval(fetchData, interval);

    return () => {
      isMounted = false;
      clearInterval(intervalId);
    };

  }, [pendingDocuments, interval]);

  return { documentStatuses };
};

export default useDocumentStatusPoller;