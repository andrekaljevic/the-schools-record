import { handle, type Env } from '../lib/handler';
export const onRequest = (context: { request: Request; env: Env }): Promise<Response> => handle('correction-report', context.request, context.env);
