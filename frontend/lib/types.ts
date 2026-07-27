export interface Author {
  name: string;
  degree: string;
  universities: string;
  email: string;
  github: string;
  orcid: string;
}

export const author: Author = {
  name: "Abdullah Al Mamun",
  degree: "M.Sc. & B.Sc. in Software Engineering",
  universities: "TU Wien (Vienna, Austria) & Daffodil International University",
  email: "mamun.swe.de@gmail.com",
  github: "https://github.com/abbysweb",
  orcid: "https://orcid.org/0009-0006-7473-0024",
};

export interface Stats {
  height: number;
  tipId: string;
  peerCount: number;
  mempoolSize: number;
  uptime: number;
  blocksTotal: number;
}

export interface Block {
  id: string;
  height: number;
  timestamp: number;
  txCount: number;
  miner: string;
  nonce: string;
  target: string;
  previd: string | null;
  txids: string[];
}

export interface Transaction {
  txid: string;
  inputs: { outpoint: { txid: string; index: number }; sig: string }[];
  outputs: { pubkey: string; value: number }[];
  height?: number;
}

export interface Peer {
  host: string;
  port: number;
  connected: boolean;
  connectedSince?: number;
}

export interface ChainTip {
  blockid: string;
  height: number;
}

export interface MempoolEntry {
  txid: string;
  inputsCount: number;
  outputsCount: number;
  totalValue: number;
}

export interface WsMessage {
  type: "new_block" | "new_tx" | "reorg" | "peer_update";
  data: Record<string, unknown>;
}
