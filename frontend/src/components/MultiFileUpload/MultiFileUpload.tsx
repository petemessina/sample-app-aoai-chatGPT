import { useState, ChangeEvent, useEffect, useRef } from 'react'
import { Stack, PrimaryButton, FontIcon, MessageBar, MessageBarType } from '@fluentui/react'
import { CustomModal } from '../CustomModal'
import { Card } from '../Card'
import styles from './MultiFileUpload.module.css'
import { uploadFile } from '../../api'

enum FileUploadStatus {
  WaitingToBeIndexed = "waiting to be indexed",
  Uploading = "uploading",
  Uploaded = "uploaded",
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
  onModalDismiss: (ev?: React.MouseEvent<HTMLButtonElement | HTMLElement>) => any;
}

export const MultiFileUpload = ({ isModalOpen, onModalDismiss }: Props) => {
  const [uploadedFiles, setUploadedFiles] = useState<Array<FileDetails>>([]);
  const [messageOptions, setMessageOptions] = useState<MessageOptions>({ message: 'All files have been uploaded successfully', messageType: MessageBarType.success, isVisible: false });
  const [uploading, setUploading] = useState<boolean>(false);
  const prevUploadingRef = useRef<boolean>(false);
  const prevUploading = prevUploadingRef.current;

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

    const fileDetails = Array.from(newFiles).map(file => ({
      status: FileUploadStatus.WaitingToBeIndexed,
      file: file,
    }));

    setUploadedFiles([...uploadedFiles, ...fileDetails])
    e.target.value = ""
  }
  
  const deleteSelectedFile = (fileName: string) => { 
    const newFiles = uploadedFiles.filter(fileDetails => fileDetails.file.name !== fileName);
    setUploadedFiles(newFiles);
  }

  const uploadFiles = async () => {
    
    setUploading(true);

    for (const fileDetail of uploadedFiles) {

      updateFileStatus(fileDetail.file.name, FileUploadStatus.Uploading);

      const uploadResult = await uploadFile(fileDetail.file);
      const updatedStatus = uploadResult.isUploaded ? FileUploadStatus.Uploaded : FileUploadStatus.FailedToUpload;

      if(updatedStatus === FileUploadStatus.FailedToUpload) {
        setMessageOptions({ ...messageOptions, message: 'Failed to upload some files', messageType: MessageBarType.error });
      }

      updateFileStatus(fileDetail.file.name, updatedStatus);
    }

    setUploading(false);
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
  
  return (
    <CustomModal isOpen={isModalOpen} onClose={onModalClose} title="Multiple File Upload With Preview">
      <Card>
        <Stack>
          <div className={styles.messageBarContainer} style={{display: messageOptions.isVisible ? 'block' : 'none'}}>
            <MessageBar messageBarType={messageOptions.messageType}>
              {messageOptions.message}
            </MessageBar>
          </div>
          <div className={styles.fileUploadBox}>
            <input type="file" id="fileUpload" className={styles.fileUploadInput} onChange={inputChange} multiple />
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
            <PrimaryButton text="Index Files" onClick={uploadFiles} />
          </div>
        </Stack>
      </Card>
    </CustomModal>
  )
}