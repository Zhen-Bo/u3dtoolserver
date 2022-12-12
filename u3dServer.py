import uvicorn
import UnityPy
import io
from fastapi import FastAPI, File, UploadFile
from fastapi.responses import StreamingResponse,HTMLResponse
from core.bundle import Bundle
from PIL import Image


app = FastAPI()

def changeAssetByFile(bundle:io.BytesIO,assetFile:UploadFile) -> io.BytesIO:
    u3dAsset = UnityPy.load(bundle.read())
    for obj in u3dAsset.objects:
        if obj.read().name == assetFile.filename.split(".")[0]:
            data = obj.read()
            pil_img = Image.open(assetFile.file)
            data.image = pil_img
            data.save()
    return io.BytesIO(u3dAsset.file.save())

@app.post("/Nikke/Decrypt")
async def decryptBundle(assetBundle: UploadFile):
    """Decrypt Encrypted Bundle

    Args:
        assetBundle (AssetBundle, optional): Encrypted AssetBubdle.

    Returns:
        AssetBundle: Decrypted AssetBundle
    """
    if not assetBundle:
        return {"message": "No file sent"}
    else:
        encryHeader: Bundle = Bundle(assetBundle.file)
        decryptedData = encryHeader.decryptBundle()
        return StreamingResponse(
            decryptedData,
            headers={
                "Content-Disposition": f"attachment; filename={assetBundle.filename}.unity3d"
            },
        )


@app.post("/Nikke/Encrypt")
async def encryptBundle(assetBundle: UploadFile):
    """Encrypt Unencrypted Bundle

    Args:
        assetBundle (AssetBundle, optional): Unencrypted AssetBubdle.

    Returns:
        AssetBundle: Encrypted AssetBundle
    """
    if not assetBundle:
        return {"message": "No file sent"}
    else:
        encryHeader: Bundle = Bundle(assetBundle.file)
        encryptedData = encryHeader.encryptBundle()
        return StreamingResponse(
            encryptedData,
            headers={
                "Content-Disposition": f"attachment; filename={assetBundle.filename.split('.')[0]}"
            },
        )

@app.post("/Nikke")
async def editBundle(assetBundle: UploadFile,assetFile: UploadFile):
    """replace asset in encrypted/Unencrypted AssetBundle

    Args:  
        assetBundle (AssetBundle, optional): can be encrypt or Unencrypted..  
        assetFile (png/txt, optional): the file you want to replace in bundle.  

    Returns:  
        AssetBundle: Eecrypted AssetBundle with replaced Asset
    """
    if not assetBundle:
        return {"message": "No file sent"}
    else:
        magicWord = assetBundle.file.read(4)
        assetBundle.file.seek(0)
        
        if magicWord != b'NKAB' and magicWord != b'Unit':
            return HTMLResponse(status_code=422)
        originBundle: Bundle = Bundle(assetBundle.file)
        if magicWord == b'NKAB':
            data = originBundle.decryptBundle()
        elif magicWord == b'Unit':
            data = assetBundle.file
    editedData = changeAssetByFile(data,assetFile)
    editedBundle:Bundle = Bundle(editedData)
    repackedBundle = editedBundle.encryptBundle()

    return StreamingResponse(
        repackedBundle,
        headers={
            "Content-Disposition": f"attachment; filename={assetBundle.filename}"
        },
    )

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
