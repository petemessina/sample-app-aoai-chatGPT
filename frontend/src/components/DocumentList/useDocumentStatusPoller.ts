import { useState, useEffect, useRef } from 'react';
import { getDocumentStatuses, UploadedDocument, DocumentStatusState } from '../../api';

type UploadedDocumentState = UploadedDocument & {
  pollingCount: number
}

const useDocumentStatusPoller = (pendingDocuments: UploadedDocument[], interval: number, maxPollPerDocument: number) => {
  const [documentStatuses, setDocumentStatuses] = useState<UploadedDocumentState[]>(pendingDocuments.map(doc => ({ ...doc, pollingCount: 0 })));
  const documentStatusesRef = useRef(documentStatuses);

  useEffect(() => {
    documentStatusesRef.current = documentStatuses;
  }, [documentStatuses]);

  useEffect(() => {
    let isMounted = true;

    const fetchData = async () => {
      if (documentStatusesRef.current && documentStatusesRef.current.length > 0 && isMounted) {
        const documentStatusData = await getDocumentStatuses(documentStatusesRef.current.map(doc => doc.id)) ?? [];
        const updatedDocumentStatuses = documentStatusData.map(doc => {
          const pendingDocument = documentStatusesRef.current.find(pd => pd.id === doc.id) || { ...doc, pollingCount: 0 };

          const newPollingCount = (pendingDocument.pollingCount || 0) + 1;

          if (newPollingCount >= maxPollPerDocument) {
            console.log(`Max polling count reached for document ID: ${doc.id}`);
            return { ...pendingDocument, pollingCount: newPollingCount, status: DocumentStatusState.PollingTimeout };
          }

          return {
            ...pendingDocument,
            pollingCount: newPollingCount
          };
        });

        setDocumentStatuses(updatedDocumentStatuses);
      }
    };

    fetchData();
    const intervalId = setInterval(fetchData, interval);

    return () => {
      isMounted = false;
      clearInterval(intervalId);
    };
  }, [interval, maxPollPerDocument]);

  useEffect(() => {
    const areArraysTheSame = pendingDocuments.every(item1 => documentStatuses.some(item2 => item1.id === item2.id));

    if (!areArraysTheSame || pendingDocuments.length !== documentStatuses.length) {
      setDocumentStatuses(pendingDocuments.map(doc => ({ ...doc, pollingCount: 0 })));
    }
  }, [pendingDocuments]);

  return { documentStatuses };
};

export default useDocumentStatusPoller;