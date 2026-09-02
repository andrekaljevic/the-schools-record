import { handle, type Env } from '../lib/handler';
export const onRequest = (context: { request: Request; env: Env }): Promise<Response> => handle('professional-enquiry', context.request, context.env);
