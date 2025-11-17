'use client'

import { useState } from 'react'
import { Upload } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { fundingService, handleApiError } from '@/lib/api'

interface ProofUploadProps {
  pairId: string
  onSuccess: () => void
}

export default function ProofUpload({ pairId, onSuccess }: ProofUploadProps) {
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [uploading, setUploading] = useState(false)

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      // Validate file size (max 5MB)
      if (file.size > 5 * 1024 * 1024) {
        alert('File size must be less than 5MB')
        return
      }
      setSelectedFile(file)
    }
  }

  const handleUpload = async () => {
    if (!selectedFile) {
      alert('Please select a file')
      return
    }

    try {
      setUploading(true)
      await fundingService.uploadProof(pairId, selectedFile)
      setSelectedFile(null)
      alert('Proof uploaded successfully!')
      onSuccess()
    } catch (err) {
      alert(handleApiError(err))
    } finally {
      setUploading(false)
    }
  }

  return (
    <div className="space-y-2">
      <Label htmlFor={`proof-${pairId}`}>Upload Proof of Payment</Label>
      <div className="flex gap-2">
        <Input
          id={`proof-${pairId}`}
          type="file"
          accept="image/*,.pdf"
          onChange={handleFileChange}
          disabled={uploading}
          className="flex-1"
        />
        <Button
          size="sm"
          onClick={handleUpload}
          disabled={uploading || !selectedFile}
        >
          <Upload className="h-4 w-4 mr-1" />
          {uploading ? 'Uploading...' : 'Upload'}
        </Button>
      </div>
      <p className="text-xs text-gray-500">
        {selectedFile
          ? `Selected: ${selectedFile.name} (${(selectedFile.size / 1024).toFixed(1)} KB)`
          : 'Accepted: Images (JPG, PNG, GIF, WebP) or PDF. Max 5MB'
        }
      </p>
    </div>
  )
}
