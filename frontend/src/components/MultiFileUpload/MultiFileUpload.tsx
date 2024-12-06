import { useState, ChangeEvent, useEffect, useRef, useContext } from 'react'
import { Stack, PrimaryButton, FontIcon, MessageBar, MessageBarType, TextField } from '@fluentui/react'
import { CustomModal } from '../CustomModal'
import { Card } from '../Card'
import styles from './MultiFileUpload.module.css'
import { uploadFile, generateConversationPlaceholder, DocumentStatusState } from '../../api'
import { AppStateContext } from "../../state/AppProvider";

enum FileUploadStatus {
  WaitingToBeIndexed = "waiting to be indexed",
  Uploading = "uploading",
  Uploaded = "Uploaded",
  FailedToUpload = "failed to upload",
  Indexed = "indexed",
  FailedToIndex = "failed to index",
}

interface FileDetails {
  file: File;
  status: FileUploadStatus
}

interface MessageOptions {
  message: string;
  messageType: MessageBarType;
  isVisible: boolean;
}

interface Props {
  isModalOpen: boolean,
  conversationId?: string;
  onModalDismiss: (ev?: React.MouseEvent<HTMLButtonElement | HTMLElement>) => any;
}

export const MultiFileUpload = ({ isModalOpen, conversationId, onModalDismiss }: Props) => {
  const appStateContext = useContext(AppStateContext)
  const defaultMessages = { message: 'All files have been uploaded successfully', messageType: MessageBarType.success, isVisible: false };
  const [uploadedFiles, setUploadedFiles] = useState<Array<FileDetails>>([]);
  const [messageOptions, setMessageOptions] = useState<MessageOptions>(defaultMessages);
  const [uploading, setUploading] = useState<boolean>(false);
  const [conversationTitle, setConversationTitle] = useState('');
  const [conversationTitleErrorMessage, setConversationTitleErrorMessage] = useState('');
  const prevUploadingRef = useRef<boolean>(false);
  const prevUploading = prevUploadingRef.current;
  const acceptedFileTypes = appStateContext?.state.frontendSettings?.valid_document_extensions ?? [];

  useEffect(() => {
    prevUploadingRef.current = uploading;
  }, [uploading]);

  useEffect(() => {
    if(prevUploading && !uploading) {
      setMessageOptions({ ...messageOptions, isVisible: true });
      
      setTimeout(() => {
        setMessageOptions({ ...messageOptions, isVisible: false });
      }, 15000);
    }
  }, [uploading, prevUploading])

  const inputChange = (e: ChangeEvent<HTMLInputElement>) => {
    const newFiles = e.target.files;

    if (!newFiles) {
      return;
    }

    const fileDetails = Array.from(newFiles).reduce<FileDetails[]>((validFiles, file) => {
      const fileExtension = file.name.split('.').pop()?.toLowerCase();
      let invalidFileFound = false;

      if (fileExtension && acceptedFileTypes.includes(`.${fileExtension}`)) {
        validFiles.push(({
          status: FileUploadStatus.WaitingToBeIndexed,
          file: file,
        }));
      } else {
        invalidFileFound = true;
      }

      if(invalidFileFound) {
        setMessageOptions({ ...messageOptions, isVisible: true, message: 'Some file formats are invalid.', messageType: MessageBarType.error });
      }

      return validFiles;
    }, []);

    setUploadedFiles([...uploadedFiles, ...fileDetails])
    e.target.value = ""
  }
  
  const deleteSelectedFile = (fileName: string) => { 
    const newFiles = uploadedFiles.filter(fileDetails => fileDetails.file.name !== fileName);
    setUploadedFiles(newFiles);
  }

  const onIndexClick = async () => {
    if(!conversationId){

      if(!conversationTitle.trim()) {
        setConversationTitleErrorMessage('Conversation title is required');
        return;
      }
      const response = await generateConversationPlaceholder(conversationTitle)

      if(response.ok) {
        const payload = await response.json();
        const now = new Date();

        conversationId = payload.conversationId;

        if(!conversationId) {
          setMessageOptions({ ...messageOptions, message: 'Failed to create conversation', messageType: MessageBarType.error });
          return;
        }        
        appStateContext?.dispatch({ type: 'UPDATE_CURRENT_CHAT_AND_HISTORY', payload: { id: conversationId, title: conversationTitle, messages: [], date: now.toISOString()} })
        uploadFiles();
      } else {
        setMessageOptions({ ...messageOptions, message: 'Failed to create conversation', messageType: MessageBarType.error });
      }
      
    } else {
      uploadFiles();
    }
  }

  const uploadFiles = async () => {
    
    setUploading(true);

    for (const fileDetail of uploadedFiles) {

      updateFileStatus(fileDetail.file.name, FileUploadStatus.Uploading);

      const uploadResult = await uploadFile(fileDetail.file, conversationId);
      const updatedStatus = uploadResult.isUploaded ? FileUploadStatus.Uploaded : FileUploadStatus.FailedToUpload;

      appStateContext?.dispatch({ 
        type: 'UPDATE_PENDING_DOCUMENTS', 
        payload: [{ 
          id: uploadResult.document_status.id, 
          conversationId: uploadResult.document_status.conversationId,
          fileName: uploadResult.document_status.fileName,
          status: uploadResult.document_status.status as DocumentStatusState
        }]
      });

      if(updatedStatus === FileUploadStatus.FailedToUpload) {
        setMessageOptions({ ...messageOptions, message: 'Failed to upload some files', messageType: MessageBarType.error });
      }

      updateFileStatus(fileDetail.file.name, updatedStatus);
    }

    setUploading(false);
    setTimeout(() => {
      onModalClose();
    }, 5000);
  }

  const formatFileSize = (size: number): string => {
    const units = ['Bytes', 'KB', 'MB', 'GB'];
    let unitIndex = 0;

    while (size >= 1024 && unitIndex < units.length - 1) {
      size /= 1024;
      unitIndex++;
    }

    return `${size.toFixed(2)} ${units[unitIndex]}`;
  }

  const convertFileLastModified = (lastModified: number): string => {
    const lastModifiedDate = new Date(lastModified);
    return lastModifiedDate.toLocaleString('en-US');
  }

  const onModalClose = (ev?: React.MouseEvent<HTMLButtonElement | HTMLElement>) => {
    setMessageOptions(defaultMessages);
    setConversationTitle('');
    setUploadedFiles([]);
    onModalDismiss(ev);
  }

  const updateFileStatus = (fileName: string, currentStatus: FileUploadStatus) => {
    setUploadedFiles(prevFiles =>
      prevFiles.map(fileDetails =>
        fileDetails.file.name === fileName ? { ...fileDetails, status: currentStatus } : fileDetails
      )
    );
  }
  
  const isButtonDisabled = () => {
    return uploading || uploadedFiles.length === 0 || (conversationId === undefined && !conversationTitle.trim()) || uploadedFiles.some(file => file.status === FileUploadStatus.Uploading || file.status === FileUploadStatus.Uploaded);
  }

  return (
    <CustomModal isOpen={isModalOpen} onClose={onModalClose} title="Multiple File Upload With Preview">
      <Card>
        <Stack>
          <div className={styles.messageBarContainer} style={{display: messageOptions.isVisible ? 'block' : 'none'}}>
            <MessageBar messageBarType={messageOptions.messageType}>
              {messageOptions.message}
            </MessageBar>
          </div>
          <div className={styles.conversationTitleContainer} style={{ display: (conversationId ?? '').trim() ? "none" : "block" }}>
            <TextField label="Conversation Title" value={conversationTitle} errorMessage={conversationTitleErrorMessage} onChange={(e, newValue) => setConversationTitle(newValue ?? '')} required />
          </div>
          <div className={styles.fileUploadBox}>
            <input type="file" id="fileUpload" className={styles.fileUploadInput} onChange={inputChange} accept={acceptedFileTypes.join(", ")} multiple />
            <span>Drag and drop or <span className={styles.fileLink}>Choose your files</span></span>
          </div>
          <div className={styles.fileAttachmentContainer}>
            {
              uploadedFiles.map((data, index) => {
                const { name, lastModified, size } = data.file;
                return (
                  <div className={styles.fileActionBox} key={name}>
                    <FontIcon
                      className={styles.fileImage}
                      iconName={'Document'}
                      aria-label='Document'
                    />
                    <div className={styles.fileDetail}>
                      <h6>{name}</h6>
                      <p></p>
                      <p><span>Size : {formatFileSize(size)}</span> <span className="ml-2">Modified Time : {convertFileLastModified(lastModified)}</span></p>
                      <p><span>Status : {data.status}</span></p>
                      <div style={{display: data.status === FileUploadStatus.WaitingToBeIndexed ? 'block' : 'none'}} className={styles.fileActions}>
                        <button type="button" className={styles.fileActionButton} onClick={() => deleteSelectedFile(name)}>Delete</button>
                      </div>
                    </div>
                  </div>
                )
              })
            }
          </div>
          <div className={styles.boxContainer}>
            <PrimaryButton text="Index Files" onClick={onIndexClick} disabled={isButtonDisabled()} />
          </div>
        </Stack>
      </Card>
    </CustomModal>
  )
}