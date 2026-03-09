import html2canvas from 'html2canvas';
import QRCode from 'qrcode';

type ShareCardOptions = {
  element: HTMLElement;
  deepLink: string;
  filename: string;
  qrCaption?: string;
  footerTitle?: string;
  footerMeta?: string;
};

function drawFittedCenteredText(
  ctx: CanvasRenderingContext2D,
  text: string,
  x: number,
  y: number,
  maxWidth: number,
  startSize: number,
  minSize: number,
) {
  let size = startSize;
  while (size > minSize) {
    ctx.font = `${size}px "Noto Sans SC", sans-serif`;
    if (ctx.measureText(text).width <= maxWidth) break;
    size -= 1;
  }
  ctx.font = `${Math.max(size, minSize)}px "Noto Sans SC", sans-serif`;
  ctx.fillText(text, x, y, maxWidth);
}

async function loadImage(src: string): Promise<HTMLImageElement> {
  return new Promise((resolve, reject) => {
    const img = new Image();
    img.onload = () => resolve(img);
    img.onerror = () => reject(new Error('Image load failed'));
    img.src = src;
  });
}

export async function downloadShareCard(options: ShareCardOptions): Promise<void> {
  const { element, deepLink, filename, qrCaption, footerTitle, footerMeta } = options;

  const elementCanvas = await html2canvas(element, {
    backgroundColor: null,
    scale: Math.min(2, window.devicePixelRatio || 1),
    useCORS: true,
    logging: false,
    onclone: (doc) => {
      doc.querySelectorAll('[data-share-exclude="true"]').forEach((node) => {
        (node as HTMLElement).style.display = 'none';
      });
    },
  });

  const qrDataUrl = await QRCode.toDataURL(deepLink, {
    width: 280,
    margin: 1,
    errorCorrectionLevel: 'M',
    color: {
      dark: '#1a1a1a',
      light: '#faf8f3ff',
    },
  });

  const qrImage = await loadImage(qrDataUrl);

  const outerPadding = Math.round(elementCanvas.width * 0.04);
  const footerHeight = Math.round(elementCanvas.height * 0.23);
  const posterCanvas = document.createElement('canvas');
  posterCanvas.width = elementCanvas.width + outerPadding * 2;
  posterCanvas.height = elementCanvas.height + footerHeight + outerPadding * 2;
  const ctx = posterCanvas.getContext('2d');
  if (!ctx) throw new Error('Canvas context unavailable');

  ctx.fillStyle = '#f5f0e6';
  ctx.fillRect(0, 0, posterCanvas.width, posterCanvas.height);

  const cardX = outerPadding;
  const cardY = outerPadding;
  ctx.fillStyle = '#e9e2d2';
  ctx.fillRect(cardX + 8, cardY + 8, elementCanvas.width, elementCanvas.height);
  ctx.drawImage(elementCanvas, cardX, cardY);

  const footerY = cardY + elementCanvas.height;
  ctx.fillStyle = '#f5f0e6';
  ctx.fillRect(cardX, footerY, elementCanvas.width, footerHeight);
  ctx.fillStyle = '#2d2d2d';
  ctx.fillRect(cardX, footerY, elementCanvas.width, 2);

  const qrSize = Math.round(footerHeight * 0.72);
  const innerPadding = Math.round(qrSize * 0.1);
  const outerMargin = Math.round(footerHeight * 0.14);
  const captionHeight = qrCaption ? Math.round(qrSize * 0.22) : 0;

  const blockWidth = qrSize + innerPadding * 2;
  const blockHeight = qrSize + innerPadding * 2 + captionHeight;
  const blockX = cardX + elementCanvas.width - blockWidth - outerMargin;
  const blockY = footerY + Math.round((footerHeight - blockHeight) / 2) + 8;

  ctx.fillStyle = 'rgba(250,248,243,0.96)';
  ctx.fillRect(blockX, blockY, blockWidth, blockHeight);
  ctx.strokeStyle = 'rgba(45,45,45,0.38)';
  ctx.lineWidth = 2;
  ctx.strokeRect(blockX, blockY, blockWidth, blockHeight);

  if (qrCaption) {
    ctx.fillStyle = '#2d2d2d';
    const captionMaxWidth = blockWidth - 12;
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    drawFittedCenteredText(
      ctx,
      qrCaption,
      blockX + blockWidth / 2,
      blockY + captionHeight / 2 + 2,
      captionMaxWidth,
      Math.max(11, Math.round(qrSize * 0.115)),
      9,
    );
  }

  const qrX = blockX + innerPadding;
  const qrY = blockY + captionHeight + innerPadding;
  ctx.drawImage(qrImage, qrX, qrY, qrSize, qrSize);

  const textX = cardX + outerMargin;
  const titleY = footerY + Math.round(footerHeight * 0.44);
  const metaY = footerY + Math.round(footerHeight * 0.7);
  const textMaxWidth = blockX - textX - outerMargin;

  if (footerTitle) {
    ctx.fillStyle = '#1f1a15';
    ctx.font = `700 ${Math.max(20, Math.round(footerHeight * 0.17))}px "Noto Sans SC", sans-serif`;
    ctx.textAlign = 'left';
    ctx.textBaseline = 'middle';
    ctx.fillText(footerTitle, textX, titleY, textMaxWidth);
  }

  if (footerMeta) {
    ctx.fillStyle = '#6b5c4d';
    ctx.font = `500 ${Math.max(14, Math.round(footerHeight * 0.115))}px "Noto Sans SC", sans-serif`;
    ctx.textAlign = 'left';
    ctx.textBaseline = 'middle';
    ctx.fillText(footerMeta, textX, metaY, textMaxWidth);
  }

  const blob = await new Promise<Blob | null>((resolve) => posterCanvas.toBlob(resolve, 'image/png', 0.95));
  if (!blob) throw new Error('Poster generation failed');

  const objectUrl = URL.createObjectURL(blob);
  const anchor = document.createElement('a');
  anchor.href = objectUrl;
  anchor.download = filename;
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  setTimeout(() => URL.revokeObjectURL(objectUrl), 1000);
}
