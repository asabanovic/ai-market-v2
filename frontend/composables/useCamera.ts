/**
 * Composable for camera functionality using Capacitor Camera plugin.
 * Uses native camera on mobile (with back camera by default), falls back to HTML input on web.
 */
import { Camera, CameraResultType, CameraSource, CameraDirection } from '@capacitor/camera'
import { Capacitor } from '@capacitor/core'

export interface CameraPhoto {
  file: File
  dataUrl: string
}

export function useCamera() {
  const isNative = Capacitor.isNativePlatform()

  /**
   * Take a photo using the camera (back camera by default)
   * @returns Promise with the captured photo as File and dataUrl
   */
  async function takePhoto(): Promise<CameraPhoto | null> {
    if (!isNative) {
      // On web, return null - component should use HTML input fallback
      return null
    }

    try {
      const photo = await Camera.getPhoto({
        quality: 90,
        allowEditing: false,
        resultType: CameraResultType.DataUrl,
        source: CameraSource.Camera,
        direction: CameraDirection.Rear, // Use back camera for product photos
        saveToGallery: false,
        correctOrientation: true,
      })

      if (!photo.dataUrl) {
        throw new Error('No photo data received')
      }

      // Convert dataUrl to File
      const file = await dataUrlToFile(photo.dataUrl, `photo_${Date.now()}.jpg`)

      return {
        file,
        dataUrl: photo.dataUrl
      }
    } catch (error: any) {
      // User cancelled or error occurred
      if (error.message?.includes('User cancelled')) {
        return null
      }
      console.error('Camera error:', error)
      throw error
    }
  }

  /**
   * Pick photo from gallery
   * @returns Promise with the selected photo as File and dataUrl
   */
  async function pickFromGallery(): Promise<CameraPhoto | null> {
    if (!isNative) {
      // On web, return null - component should use HTML input fallback
      return null
    }

    try {
      const photo = await Camera.getPhoto({
        quality: 90,
        allowEditing: false,
        resultType: CameraResultType.DataUrl,
        source: CameraSource.Photos,
        correctOrientation: true,
      })

      if (!photo.dataUrl) {
        throw new Error('No photo data received')
      }

      // Convert dataUrl to File
      const file = await dataUrlToFile(photo.dataUrl, `photo_${Date.now()}.jpg`)

      return {
        file,
        dataUrl: photo.dataUrl
      }
    } catch (error: any) {
      // User cancelled or error occurred
      if (error.message?.includes('User cancelled')) {
        return null
      }
      console.error('Gallery error:', error)
      throw error
    }
  }

  /**
   * Check camera permissions
   */
  async function checkPermissions() {
    if (!isNative) return { camera: 'granted', photos: 'granted' }

    try {
      const permissions = await Camera.checkPermissions()
      return permissions
    } catch (error) {
      console.error('Permission check error:', error)
      return { camera: 'denied', photos: 'denied' }
    }
  }

  /**
   * Request camera permissions
   */
  async function requestPermissions() {
    if (!isNative) return { camera: 'granted', photos: 'granted' }

    try {
      const permissions = await Camera.requestPermissions()
      return permissions
    } catch (error) {
      console.error('Permission request error:', error)
      return { camera: 'denied', photos: 'denied' }
    }
  }

  return {
    isNative,
    takePhoto,
    pickFromGallery,
    checkPermissions,
    requestPermissions
  }
}

/**
 * Convert a data URL to a File object
 */
async function dataUrlToFile(dataUrl: string, filename: string): Promise<File> {
  const response = await fetch(dataUrl)
  const blob = await response.blob()
  return new File([blob], filename, { type: blob.type || 'image/jpeg' })
}
