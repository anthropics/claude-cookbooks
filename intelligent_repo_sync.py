#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Intelligent Repository Synchronization System
智能倉庫同步系統 - 基於邏輯架構原理的全域同步

核心功能：
1. 邏輯架構提取（concepts, reasoning chains, causal relations）
2. 粒子化記憶（SimHash64 + Merkle Chain）
3. 注意力機制（ParticleAttention）
4. 全域語意掃描（跨倉庫結構分析）

Author: MR.liou × Claude
怎麼過去，就怎麼回來

基於 MrLiouWord 粒子系統整合字典 v2.0
SEED(X) = STORE(RECURSE(FLOW(MARK(STRUCTURE(X)))))
"""

import os
import sys
import json
import hashlib
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Set
from datetime import datetime
from dataclasses import dataclass, field
import subprocess
import re
from collections import defaultdict
import struct
import math

# ============================================
# 粒子類型常量（基於粒子系統字典 v2）
# ============================================

# 五種基礎粒子
PARTICLE_ANCHOR = 0x01      # Ⓟ 錨粒子 - 跨層級定位錨點
PARTICLE_SEED = 0x02        # Ⓘ 種子粒子 - 核心語義承載者
PARTICLE_JUMP = 0x04        # ↯ 跳粒子 - 跨Reality跳躍節點
PARTICLE_MEMORY = 0x08      # ⧫ 記憶粒子 - 儲存上下文和歷史
PARTICLE_FUSION = 0x10      # ⨁ 融合粒子 - 不同粒子類型間的融合器

# 擴展粒子類型
PARTICLE_CTX = 0x01         # 上下文粒子
PARTICLE_TOOL = 0x02        # 工具粒子
PARTICLE_AUTH = 0x04        # 授權粒子
PARTICLE_EXEC = 0x08        # 執行粒子
PARTICLE_SEC = 0x10         # 安全粒子
PARTICLE_PERSONA = 0x40     # 人格粒子
PARTICLE_RHYTHM = 0x80      # 節奏粒子

# 粒子運算宏
def AI_MASK(x): return x & 0x0F
def AI_TRUST(x, y): return (x & 0x04) and (y & 0x10)
def AI_OK(x): return (x & 0x08) and not (x & 0x04)
def COMBINE(x, y): return x | y
def EXTRACT(x, y): return x & y
def TRANSFORM(x, f): return f(x)


# ============================================
# 第一部分：SimHash64 指紋系統
# ============================================

class SimHash64:
    """
    SimHash64 語義指紋生成器
    
    基於粒子系統的語義壓縮：
    - 64位元指紋
    - 漢明距離計算相似度
    - 支援增量更新
    """
    
    def __init__(self, hash_bits: int = 64):
        self.hash_bits = hash_bits
        self.fingerprint = 0
    
    def _tokenize(self, text: str) -> List[str]:
        """
        分詞處理
        支援中英文混合
        """
        # 英文：按空格和標點分詞
        # 中文：按字符分詞（簡化處理）
        tokens = []
        
        # 提取英文單詞
        english_words = re.findall(r'[a-zA-Z_][a-zA-Z0-9_]*', text)
        tokens.extend(english_words)
        
        # 提取中文（每2-3字為一個token）
        chinese_chars = re.findall(r'[\u4e00-\u9fff]+', text)
        for chars in chinese_chars:
            for i in range(len(chars) - 1):
                tokens.append(chars[i:i+2])
        
        return tokens
    
    def _hash_token(self, token: str) -> int:
        """對單個token生成hash值"""
        h = hashlib.md5(token.encode('utf-8')).digest()
        # 取前8字節作為64位整數
        return struct.unpack('<Q', h[:8])[0]
    
    def compute(self, text: str) -> int:
        """
        計算文本的SimHash64指紋
        
        算法：
        1. 分詞
        2. 對每個詞計算hash
        3. 加權累加（出現次數為權重）
        4. 降維到64位
        """
        tokens = self._tokenize(text)
        if not tokens:
            return 0
        
        # 統計詞頻
        token_weights = defaultdict(int)
        for token in tokens:
            token_weights[token] += 1
        
        # 初始化64維向量
        vector = [0] * self.hash_bits
        
        # 累加每個token的貢獻
        for token, weight in token_weights.items():
            token_hash = self._hash_token(token)
            for i in range(self.hash_bits):
                bit = (token_hash >> i) & 1
                if bit:
                    vector[i] += weight
                else:
                    vector[i] -= weight
        
        # 降維：正數為1，負數為0
        fingerprint = 0
        for i in range(self.hash_bits):
            if vector[i] > 0:
                fingerprint |= (1 << i)
        
        self.fingerprint = fingerprint
        return fingerprint
    
    @staticmethod
    def hamming_distance(fp1: int, fp2: int) -> int:
        """計算兩個指紋的漢明距離"""
        xor = fp1 ^ fp2
        distance = 0
        while xor:
            distance += xor & 1
            xor >>= 1
        return distance
    
    @staticmethod
    def similarity(fp1: int, fp2: int, bits: int = 64) -> float:
        """計算相似度（0-1）"""
        distance = SimHash64.hamming_distance(fp1, fp2)
        return 1.0 - (distance / bits)
    
    def to_hex(self) -> str:
        """返回16進制表示"""
        return f'{self.fingerprint:016x}'
    
    @classmethod
    def from_hex(cls, hex_str: str) -> 'SimHash64':
        """從16進制字符串創建"""
        instance = cls()
        instance.fingerprint = int(hex_str, 16)
        return instance


# ============================================
# 第二部分：Merkle Chain 完整性驗證
# ============================================

@dataclass
class MerkleNode:
    """Merkle 節點"""
    hash: str
    data: Optional[str] = None
    left: Optional['MerkleNode'] = None
    right: Optional['MerkleNode'] = None
    parent: Optional['MerkleNode'] = None
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())


class MerkleChain:
    """
    Merkle Chain 完整性驗證系統
    
    基於粒子系統的記憶完整性：
    - 鏈式哈希結構
    - 支援增量添加
    - 快速驗證路徑
    """
    
    def __init__(self):
        self.nodes: List[MerkleNode] = []
        self.root: Optional[MerkleNode] = None
    
    def _hash(self, data: str) -> str:
        """計算SHA256哈希"""
        return hashlib.sha256(data.encode('utf-8')).hexdigest()
    
    def _combine_hash(self, left: str, right: str) -> str:
        """合併兩個哈希"""
        return self._hash(left + right)
    
    def add(self, data: str) -> MerkleNode:
        """
        添加數據到鏈中
        
        Returns:
            新創建的葉節點
        """
        data_hash = self._hash(data)
        node = MerkleNode(hash=data_hash, data=data)
        self.nodes.append(node)
        self._rebuild_tree()
        return node
    
    def add_batch(self, data_list: List[str]) -> List[MerkleNode]:
        """批量添加"""
        new_nodes = []
        for data in data_list:
            data_hash = self._hash(data)
            node = MerkleNode(hash=data_hash, data=data)
            self.nodes.append(node)
            new_nodes.append(node)
        self._rebuild_tree()
        return new_nodes
    
    def _rebuild_tree(self):
        """重建Merkle樹"""
        if not self.nodes:
            self.root = None
            return
        
        # 葉節點層
        current_level = self.nodes.copy()
        
        # 逐層向上構建
        while len(current_level) > 1:
            next_level = []
            
            for i in range(0, len(current_level), 2):
                left = current_level[i]
                right = current_level[i + 1] if i + 1 < len(current_level) else left
                
                parent_hash = self._combine_hash(left.hash, right.hash)
                parent = MerkleNode(hash=parent_hash, left=left, right=right)
                
                left.parent = parent
                if right != left:
                    right.parent = parent
                
                next_level.append(parent)
            
            current_level = next_level
        
        self.root = current_level[0] if current_level else None
    
    def get_root_hash(self) -> Optional[str]:
        """獲取根哈希"""
        return self.root.hash if self.root else None
    
    def get_proof(self, index: int) -> List[Tuple[str, str]]:
        """
        獲取驗證路徑
        
        Returns:
            [(hash, position), ...] position為'left'或'right'
        """
        if index < 0 or index >= len(self.nodes):
            return []
        
        proof = []
        node = self.nodes[index]
        
        while node.parent:
            parent = node.parent
            if parent.left == node:
                sibling = parent.right
                position = 'right'
            else:
                sibling = parent.left
                position = 'left'
            
            if sibling and sibling != node:
                proof.append((sibling.hash, position))
            
            node = parent
        
        return proof
    
    def verify(self, data: str, proof: List[Tuple[str, str]], root_hash: str) -> bool:
        """驗證數據完整性"""
        current_hash = self._hash(data)
        
        for sibling_hash, position in proof:
            if position == 'left':
                current_hash = self._combine_hash(sibling_hash, current_hash)
            else:
                current_hash = self._combine_hash(current_hash, sibling_hash)
        
        return current_hash == root_hash
    
    def to_dict(self) -> Dict:
        """序列化為字典"""
        return {
            'root_hash': self.get_root_hash(),
            'node_count': len(self.nodes),
            'nodes': [
                {
                    'hash': node.hash,
                    'data_preview': node.data[:50] if node.data else None,
                    'timestamp': node.timestamp
                }
                for node in self.nodes
            ]
        }


# ============================================
# 第三部分：邏輯架構提取器
# ============================================

class LogicalStructureExtractor:
    """
    邏輯架構提取器
    
    從代碼/文檔中提取：
    - 核心概念（Core Concepts）
    - 因果關係（Causal Relations）
    - 推理鏈（Reasoning Chains）
    - 架構模式（Architectural Patterns）
    """
    
    def __init__(self):
        # 邏輯模式識別詞
        self.causal_markers = [
            'because', 'since', 'therefore', 'thus', 'hence', 'so',
            '因為', '所以', '因此', '從而', '導致', '引起'
        ]
        
        self.reasoning_markers = [
            'if', 'then', 'when', 'while', 'for', 'given',
            '如果', '那麼', '當', '對於', '假設', '基於'
        ]
        
        self.conclusion_markers = [
            'in conclusion', 'finally', 'therefore', 'summary',
            '總結', '結論', '綜上', '最終'
        ]
        
        # 架構模式關鍵詞（基於粒子系統字典）
        self.pattern_keywords = {
            'attention': ['attention', 'transformer', 'multi-head', 'self-attention', '注意力', 'FOCUS', 'SPREAD'],
            'memory': ['memory', 'cache', 'store', 'persist', '記憶', '存儲', 'MemoryVault', 'STORE'],
            'particle': ['particle', 'atom', 'quantum', '粒子', '原子', 'atom_t', 'δP₀'],
            'frequency': ['frequency', 'wave', 'resonance', '頻率', '共振', 'RHYTHM'],
            'merkle': ['merkle', 'hash', 'chain', 'integrity', '哈希鏈'],
            'simhash': ['simhash', 'fingerprint', 'similarity', '指紋', 'SimHash64'],
            'flow': ['flow', 'pipeline', 'stream', '流', '管道', 'FlowAgent', 'FlowSeed'],
            'layer': ['layer', 'level', 'tier', '層', '層次', 'L1', 'L2', 'L3', 'L4', 'L5', 'L6', 'L7'],
            'reality': ['reality', 'R0', 'R1', 'R2', 'R3', 'R4', '現實層', 'World'],
            'seed': ['SEED', 'STRUCTURE', 'MARK', 'FLOW', 'RECURSE', '種子', '萃取'],
            'persona': ['persona', 'personality', '人格', 'PersonaField', 'Mother'],
            'fluin': ['fluin', 'fxz', 'flpkg', 'fltnz', 'Fluin']
        }
    
    def extract_from_code(self, code: str, language: str = 'auto') -> Dict:
        """
        從代碼中提取邏輯架構
        
        Returns:
            {
                "concepts": [...],           # 核心概念
                "patterns": {...},           # 架構模式
                "relationships": [...],      # 因果關係
                "reasoning_chains": [...],   # 推理鏈
                "functions": [...],          # 函數/類定義
                "imports": [...],            # 依賴關係
                "simhash": "...",            # 語義指紋
                "particle_types": [...]      # 識別到的粒子類型
            }
        """
        structure = {
            "concepts": [],
            "patterns": defaultdict(list),
            "relationships": [],
            "reasoning_chains": [],
            "functions": [],
            "imports": [],
            "simhash": "",
            "particle_types": []
        }
        
        # 0. 計算語義指紋
        hasher = SimHash64()
        structure['simhash'] = hasher.compute(code)
        
        # 1. 提取函數/類定義（多語言支持）
        if language in ['python', 'auto']:
            structure['functions'].extend(self._extract_python_definitions(code))
            structure['imports'].extend(self._extract_python_imports(code))
        
        if language in ['typescript', 'javascript', 'auto']:
            structure['functions'].extend(self._extract_ts_definitions(code))
            structure['imports'].extend(self._extract_ts_imports(code))
        
        if language in ['rust', 'auto']:
            structure['functions'].extend(self._extract_rust_definitions(code))
        
        # 2. 提取架構模式
        for pattern_name, keywords in self.pattern_keywords.items():
            matches = []
            for keyword in keywords:
                if re.search(r'\b' + re.escape(keyword) + r'\b', code, re.IGNORECASE):
                    matches.append(keyword)
            if matches:
                structure['patterns'][pattern_name] = matches
        
        # 3. 識別粒子類型
        structure['particle_types'] = self._identify_particle_types(code)
        
        # 4. 提取注釋中的邏輯結構
        comments = self._extract_comments(code, language)
        for comment in comments:
            # 提取概念
            concepts = self._extract_concepts(comment)
            structure['concepts'].extend(concepts)
            
            # 提取因果關係
            relations = self._extract_causal_relations(comment)
            structure['relationships'].extend(relations)
            
            # 提取推理鏈
            chains = self._extract_reasoning_chains(comment)
            structure['reasoning_chains'].extend(chains)
        
        # 去重
        structure['concepts'] = list(set(structure['concepts']))
        structure['patterns'] = dict(structure['patterns'])
        
        return structure
    
    def _identify_particle_types(self, code: str) -> List[Dict]:
        """識別代碼中使用的粒子類型"""
        particle_patterns = {
            'anchor': (r'[Ⓟ]|anchor|錨粒子|ANCHOR', PARTICLE_ANCHOR),
            'seed': (r'[Ⓘ]|seed|種子粒子|SEED', PARTICLE_SEED),
            'jump': (r'[↯]|jump|跳粒子|JUMP', PARTICLE_JUMP),
            'memory': (r'[⧫]|memory|記憶粒子|MEMORY', PARTICLE_MEMORY),
            'fusion': (r'[⨁]|fusion|融合粒子|FUSION', PARTICLE_FUSION),
        }
        
        found = []
        for name, (pattern, hex_code) in particle_patterns.items():
            if re.search(pattern, code, re.IGNORECASE):
                found.append({
                    'type': name,
                    'hex': hex(hex_code),
                    'occurrences': len(re.findall(pattern, code, re.IGNORECASE))
                })
        
        return found
    
    def _extract_python_definitions(self, code: str) -> List[Dict]:
        """提取 Python 類和函數定義"""
        definitions = []
        
        # 類定義
        class_pattern = r'class\s+(\w+)\s*(?:\(([^)]*)\))?:'
        for match in re.finditer(class_pattern, code):
            definitions.append({
                'type': 'class',
                'name': match.group(1),
                'parents': [p.strip() for p in match.group(2).split(',')] if match.group(2) else [],
                'line': code[:match.start()].count('\n') + 1
            })
        
        # 函數定義
        func_pattern = r'def\s+(\w+)\s*\(([^)]*)\)'
        for match in re.finditer(func_pattern, code):
            params = []
            if match.group(2):
                for p in match.group(2).split(','):
                    p = p.strip()
                    if p and p != 'self':
                        param_name = p.split(':')[0].split('=')[0].strip()
                        params.append(param_name)
            
            definitions.append({
                'type': 'function',
                'name': match.group(1),
                'params': params,
                'line': code[:match.start()].count('\n') + 1
            })
        
        return definitions
    
    def _extract_python_imports(self, code: str) -> List[str]:
        """提取 Python 導入"""
        imports = set()
        
        # import xxx
        imports.update(re.findall(r'^import\s+([\w.]+)', code, re.MULTILINE))
        
        # from xxx import yyy
        imports.update(re.findall(r'^from\s+([\w.]+)\s+import', code, re.MULTILINE))
        
        return list(imports)
    
    def _extract_ts_definitions(self, code: str) -> List[Dict]:
        """提取 TypeScript/JavaScript 類和函數定義"""
        definitions = []
        
        # 類定義
        class_pattern = r'class\s+(\w+)(?:\s+extends\s+(\w+))?(?:\s+implements\s+([\w,\s]+))?'
        for match in re.finditer(class_pattern, code):
            definitions.append({
                'type': 'class',
                'name': match.group(1),
                'extends': match.group(2),
                'implements': [i.strip() for i in match.group(3).split(',')] if match.group(3) else [],
                'line': code[:match.start()].count('\n') + 1
            })
        
        # 函數定義 (多種形式)
        # function name(...)
        func_pattern1 = r'function\s+(\w+)\s*\(([^)]*)\)'
        for match in re.finditer(func_pattern1, code):
            definitions.append({
                'type': 'function',
                'name': match.group(1),
                'params': [p.strip().split(':')[0].strip() for p in match.group(2).split(',') if p.strip()],
                'line': code[:match.start()].count('\n') + 1
            })
        
        # const name = (...) => 或 const name = function(...)
        arrow_pattern = r'(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s*)?\(([^)]*)\)\s*(?::\s*\w+)?\s*=>'
        for match in re.finditer(arrow_pattern, code):
            definitions.append({
                'type': 'arrow_function',
                'name': match.group(1),
                'params': [p.strip().split(':')[0].strip() for p in match.group(2).split(',') if p.strip()],
                'line': code[:match.start()].count('\n') + 1
            })
        
        # interface 定義
        interface_pattern = r'interface\s+(\w+)(?:\s+extends\s+([\w,\s]+))?'
        for match in re.finditer(interface_pattern, code):
            definitions.append({
                'type': 'interface',
                'name': match.group(1),
                'extends': [i.strip() for i in match.group(2).split(',')] if match.group(2) else [],
                'line': code[:match.start()].count('\n') + 1
            })
        
        # type 定義
        type_pattern = r'type\s+(\w+)\s*='
        for match in re.finditer(type_pattern, code):
            definitions.append({
                'type': 'type_alias',
                'name': match.group(1),
                'line': code[:match.start()].count('\n') + 1
            })
        
        return definitions
    
    def _extract_ts_imports(self, code: str) -> List[str]:
        """提取 TypeScript/JavaScript 導入"""
        imports = set()
        
        # import xxx from 'yyy'
        imports.update(re.findall(r"import\s+.*?\s+from\s+['\"]([^'\"]+)['\"]", code))
        
        # import 'yyy'
        imports.update(re.findall(r"import\s+['\"]([^'\"]+)['\"]", code))
        
        # require('yyy')
        imports.update(re.findall(r"require\s*\(\s*['\"]([^'\"]+)['\"]\s*\)", code))
        
        return list(imports)
    
    def _extract_rust_definitions(self, code: str) -> List[Dict]:
        """提取 Rust 定義"""
        definitions = []
        
        # struct 定義
        struct_pattern = r'(?:pub\s+)?struct\s+(\w+)'
        for match in re.finditer(struct_pattern, code):
            definitions.append({
                'type': 'struct',
                'name': match.group(1),
                'line': code[:match.start()].count('\n') + 1
            })
        
        # fn 定義
        fn_pattern = r'(?:pub\s+)?(?:async\s+)?fn\s+(\w+)\s*(?:<[^>]*>)?\s*\(([^)]*)\)'
        for match in re.finditer(fn_pattern, code):
            definitions.append({
                'type': 'function',
                'name': match.group(1),
                'params': [p.strip().split(':')[0].strip() for p in match.group(2).split(',') if p.strip() and p.strip() != 'self' and p.strip() != '&self' and p.strip() != '&mut self'],
                'line': code[:match.start()].count('\n') + 1
            })
        
        # impl 定義
        impl_pattern = r'impl(?:<[^>]*>)?\s+(\w+)'
        for match in re.finditer(impl_pattern, code):
            definitions.append({
                'type': 'impl',
                'name': match.group(1),
                'line': code[:match.start()].count('\n') + 1
            })
        
        return definitions
    
    def _extract_comments(self, code: str, language: str) -> List[str]:
        """提取代碼註釋"""
        comments = []
        
        # 單行註釋 // 或 #
        if language in ['python', 'auto']:
            comments.extend(re.findall(r'#\s*(.+)$', code, re.MULTILINE))
        
        if language in ['typescript', 'javascript', 'rust', 'auto']:
            comments.extend(re.findall(r'//\s*(.+)$', code, re.MULTILINE))
        
        # 多行註釋 /* */ 或 """ """
        if language in ['typescript', 'javascript', 'rust', 'auto']:
            multiline = re.findall(r'/\*\s*(.*?)\s*\*/', code, re.DOTALL)
            comments.extend(multiline)
        
        if language in ['python', 'auto']:
            docstrings = re.findall(r'"""(.*?)"""', code, re.DOTALL)
            comments.extend(docstrings)
            docstrings = re.findall(r"'''(.*?)'''", code, re.DOTALL)
            comments.extend(docstrings)
        
        return comments
    
    def _extract_concepts(self, text: str) -> List[str]:
        """從文本中提取核心概念"""
        concepts = []
        
        # 提取大寫開頭的專有名詞
        proper_nouns = re.findall(r'\b([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*)\b', text)
        concepts.extend(proper_nouns)
        
        # 提取中文專有名詞（引號內的內容）
        chinese_terms = re.findall(r'「([^」]+)」|『([^』]+)』|"([^"]+)"', text)
        for match in chinese_terms:
            for term in match:
                if term:
                    concepts.append(term)
        
        # 提取 CamelCase 或 snake_case 術語
        camel_case = re.findall(r'\b([a-z]+(?:[A-Z][a-z]+)+)\b', text)
        concepts.extend(camel_case)
        
        snake_case = re.findall(r'\b([a-z]+(?:_[a-z]+)+)\b', text)
        concepts.extend(snake_case)
        
        return concepts
    
    def _extract_causal_relations(self, text: str) -> List[Dict]:
        """提取因果關係"""
        relations = []
        
        for marker in self.causal_markers:
            pattern = rf'(.{{10,50}})\s*{re.escape(marker)}\s*(.{{10,50}})'
            matches = re.findall(pattern, text, re.IGNORECASE)
            for before, after in matches:
                relations.append({
                    'cause': before.strip(),
                    'effect': after.strip(),
                    'marker': marker
                })
        
        return relations
    
    def _extract_reasoning_chains(self, text: str) -> List[Dict]:
        """提取推理鏈"""
        chains = []
        
        # if-then 模式
        if_then = re.findall(r'if\s+(.+?)\s*,?\s*then\s+(.+?)(?:\.|$)', text, re.IGNORECASE)
        for condition, result in if_then:
            chains.append({
                'type': 'conditional',
                'condition': condition.strip(),
                'result': result.strip()
            })
        
        # 如果-那麼 模式
        zh_if_then = re.findall(r'如果\s*(.+?)\s*[,，]\s*(?:那麼|則)\s*(.+?)(?:。|$)', text)
        for condition, result in zh_if_then:
            chains.append({
                'type': 'conditional',
                'condition': condition.strip(),
                'result': result.strip()
            })
        
        return chains


# ============================================
# 第四部分：粒子注意力機制
# ============================================

@dataclass
class AttentionState:
    """注意力狀態"""
    focus_target: str = ""
    handshake: bool = False
    spread_count: int = 0
    weight: float = 1.0
    history: List[str] = field(default_factory=list)


class ParticleAttention:
    """
    粒子注意力機制
    
    基於粒子系統的注意力循環：
    FOCUS → CHECK_HANDSHAKE → SPREAD → REWEIGHT
    
    直到 handshake=true 才停止
    """
    
    def __init__(self, max_iterations: int = 10):
        self.max_iterations = max_iterations
        self.state = AttentionState()
        self.attention_weights: Dict[str, float] = {}
        self.memory_particles: List[Dict] = []
    
    def focus(self, target: str, context: Dict[str, Any] = None) -> 'ParticleAttention':
        """
        聚焦階段
        
        將注意力集中到目標上
        """
        self.state.focus_target = target
        self.state.history.append(f"FOCUS: {target}")
        
        # 初始化注意力權重
        if context:
            for key in context.keys():
                self.attention_weights[key] = 0.1
        
        self.attention_weights[target] = 1.0
        
        return self
    
    def check_handshake(self, condition_fn=None) -> bool:
        """
        握手檢查階段
        
        檢查是否達到收斂條件
        """
        if condition_fn:
            self.state.handshake = condition_fn(self.state, self.attention_weights)
        else:
            # 默認條件：權重差異小於閾值
            weights = list(self.attention_weights.values())
            if weights:
                max_w = max(weights)
                min_w = min(weights)
                self.state.handshake = (max_w - min_w) < 0.1 or self.state.spread_count >= self.max_iterations
        
        self.state.history.append(f"CHECK_HANDSHAKE: {self.state.handshake}")
        return self.state.handshake
    
    def spread(self, graph: Dict[str, List[str]] = None) -> 'ParticleAttention':
        """
        擴散階段
        
        將注意力從焦點擴散到相關節點
        """
        self.state.spread_count += 1
        
        if graph and self.state.focus_target in graph:
            neighbors = graph[self.state.focus_target]
            spread_weight = self.attention_weights.get(self.state.focus_target, 1.0) * 0.5
            
            for neighbor in neighbors:
                current = self.attention_weights.get(neighbor, 0)
                self.attention_weights[neighbor] = current + spread_weight / len(neighbors)
        
        self.state.history.append(f"SPREAD: iteration {self.state.spread_count}")
        return self
    
    def reweight(self, decay: float = 0.9) -> 'ParticleAttention':
        """
        重新加權階段
        
        歸一化並衰減權重
        """
        # 衰減
        for key in self.attention_weights:
            self.attention_weights[key] *= decay
        
        # 歸一化
        total = sum(self.attention_weights.values())
        if total > 0:
            for key in self.attention_weights:
                self.attention_weights[key] /= total
        
        self.state.history.append(f"REWEIGHT: decay={decay}")
        return self
    
    def run_cycle(self, target: str, graph: Dict[str, List[str]] = None, 
                  condition_fn=None) -> Dict[str, float]:
        """
        執行完整的注意力循環
        
        FOCUS → CHECK_HANDSHAKE → SPREAD → REWEIGHT
        循環直到 handshake=true
        """
        self.focus(target)
        
        while not self.check_handshake(condition_fn):
            self.spread(graph)
            self.reweight()
        
        return self.attention_weights
    
    def get_top_k(self, k: int = 5) -> List[Tuple[str, float]]:
        """獲取注意力最高的 k 個目標"""
        sorted_weights = sorted(
            self.attention_weights.items(),
            key=lambda x: x[1],
            reverse=True
        )
        return sorted_weights[:k]
    
    def to_memory_particle(self) -> Dict:
        """將當前注意力狀態轉換為記憶粒子"""
        return {
            'type': 'attention_memory',
            'hex': hex(PARTICLE_MEMORY),
            'focus': self.state.focus_target,
            'weights': self.attention_weights.copy(),
            'iterations': self.state.spread_count,
            'timestamp': datetime.utcnow().isoformat()
        }


# ============================================
# 第五部分：全域語意掃描器
# ============================================

class GlobalSemanticScanner:
    """
    全域語意掃描器
    
    跨倉庫結構分析：
    - 掃描多個倉庫
    - 提取統一的邏輯架構
    - 建立跨倉庫關聯
    """
    
    def __init__(self):
        self.extractor = LogicalStructureExtractor()
        self.merkle_chain = MerkleChain()
        self.repo_structures: Dict[str, Dict] = {}
        self.cross_references: List[Dict] = []
    
    def scan_directory(self, path: Path, extensions: List[str] = None) -> Dict:
        """
        掃描目錄中的所有代碼文件
        
        Args:
            path: 目錄路徑
            extensions: 要掃描的文件擴展名列表
        
        Returns:
            目錄的統一結構
        """
        if extensions is None:
            extensions = ['.py', '.ts', '.js', '.rs', '.md', '.json']
        
        structure = {
            'path': str(path),
            'files': [],
            'total_concepts': [],
            'total_patterns': defaultdict(list),
            'total_functions': [],
            'cross_file_relations': []
        }
        
        for ext in extensions:
            for file_path in path.rglob(f'*{ext}'):
                # 跳過 node_modules 和隱藏目錄
                if 'node_modules' in str(file_path) or '/.' in str(file_path):
                    continue
                
                try:
                    content = file_path.read_text(encoding='utf-8')
                    
                    # 確定語言
                    lang = 'auto'
                    if ext == '.py':
                        lang = 'python'
                    elif ext in ['.ts', '.tsx']:
                        lang = 'typescript'
                    elif ext in ['.js', '.jsx']:
                        lang = 'javascript'
                    elif ext == '.rs':
                        lang = 'rust'
                    
                    # 提取結構
                    file_structure = self.extractor.extract_from_code(content, lang)
                    file_structure['file'] = str(file_path.relative_to(path))
                    
                    # 添加到 Merkle Chain
                    self.merkle_chain.add(content)
                    
                    structure['files'].append(file_structure)
                    structure['total_concepts'].extend(file_structure['concepts'])
                    structure['total_functions'].extend(file_structure['functions'])
                    
                    for pattern, matches in file_structure['patterns'].items():
                        structure['total_patterns'][pattern].extend(matches)
                    
                except Exception as e:
                    print(f"Warning: Could not process {file_path}: {e}")
        
        # 去重概念
        structure['total_concepts'] = list(set(structure['total_concepts']))
        structure['total_patterns'] = dict(structure['total_patterns'])
        
        # 分析跨文件關係
        structure['cross_file_relations'] = self._analyze_cross_file_relations(structure['files'])
        
        return structure
    
    def _analyze_cross_file_relations(self, files: List[Dict]) -> List[Dict]:
        """分析跨文件關係"""
        relations = []
        
        # 收集所有定義
        all_definitions = {}
        for file_struct in files:
            file_name = file_struct.get('file', 'unknown')
            for func in file_struct.get('functions', []):
                name = func.get('name', '')
                if name:
                    all_definitions[name] = file_name
        
        # 檢查導入關係
        for file_struct in files:
            file_name = file_struct.get('file', 'unknown')
            imports = file_struct.get('imports', [])
            
            for imp in imports:
                # 簡化：檢查是否導入了其他文件中定義的內容
                imp_base = imp.split('.')[-1]
                if imp_base in all_definitions and all_definitions[imp_base] != file_name:
                    relations.append({
                        'from': file_name,
                        'to': all_definitions[imp_base],
                        'type': 'imports',
                        'target': imp_base
                    })
        
        return relations
    
    def scan_repository(self, repo_path: str, repo_name: str = None) -> Dict:
        """掃描整個倉庫"""
        path = Path(repo_path)
        
        if not path.exists():
            raise ValueError(f"Repository path does not exist: {repo_path}")
        
        if repo_name is None:
            repo_name = path.name
        
        structure = self.scan_directory(path)
        structure['repo_name'] = repo_name
        structure['merkle_root'] = self.merkle_chain.get_root_hash()
        structure['scan_time'] = datetime.utcnow().isoformat()
        
        self.repo_structures[repo_name] = structure
        
        return structure
    
    def find_cross_repo_relations(self) -> List[Dict]:
        """查找跨倉庫關聯"""
        relations = []
        
        repo_names = list(self.repo_structures.keys())
        
        for i, repo1 in enumerate(repo_names):
            for repo2 in repo_names[i+1:]:
                struct1 = self.repo_structures[repo1]
                struct2 = self.repo_structures[repo2]
                
                # 共同概念
                common_concepts = set(struct1['total_concepts']) & set(struct2['total_concepts'])
                if common_concepts:
                    relations.append({
                        'repo1': repo1,
                        'repo2': repo2,
                        'type': 'shared_concepts',
                        'items': list(common_concepts)
                    })
                
                # 共同模式
                common_patterns = set(struct1['total_patterns'].keys()) & set(struct2['total_patterns'].keys())
                if common_patterns:
                    relations.append({
                        'repo1': repo1,
                        'repo2': repo2,
                        'type': 'shared_patterns',
                        'items': list(common_patterns)
                    })
        
        self.cross_references = relations
        return relations
    
    def generate_report(self) -> Dict:
        """生成完整的掃描報告"""
        return {
            'scan_summary': {
                'total_repos': len(self.repo_structures),
                'total_files': sum(len(s['files']) for s in self.repo_structures.values()),
                'merkle_root': self.merkle_chain.get_root_hash()
            },
            'repositories': self.repo_structures,
            'cross_repo_relations': self.cross_references,
            'generated_at': datetime.utcnow().isoformat()
        }


# ============================================
# 第六部分：SEED 萃取引擎
# ============================================

class SEEDExtractor:
    """
    SEED(X) 萃取引擎
    
    實現：SEED(X) = STORE(RECURSE(FLOW(MARK(STRUCTURE(X)))))
    
    將任意輸入萃取為粒子化種子
    """
    
    def __init__(self):
        self.structure_cache = {}
        self.mark_index = {}
        self.flow_graph = {}
        self.storage = MerkleChain()
    
    def structure(self, x: Any) -> Dict:
        """
        STRUCTURE 階段
        
        將輸入結構化為標準格式
        """
        if isinstance(x, str):
            # 字符串：分析其結構
            return {
                'type': 'string',
                'length': len(x),
                'tokens': x.split(),
                'simhash': SimHash64().compute(x)
            }
        elif isinstance(x, dict):
            return {
                'type': 'dict',
                'keys': list(x.keys()),
                'depth': self._get_dict_depth(x),
                'content': x
            }
        elif isinstance(x, list):
            return {
                'type': 'list',
                'length': len(x),
                'item_types': list(set(type(i).__name__ for i in x)),
                'content': x
            }
        else:
            return {
                'type': type(x).__name__,
                'value': str(x)
            }
    
    def _get_dict_depth(self, d: Dict, current_depth: int = 0) -> int:
        """計算字典深度"""
        if not isinstance(d, dict) or not d:
            return current_depth
        return max(self._get_dict_depth(v, current_depth + 1) for v in d.values())
    
    def mark(self, structured: Dict) -> Dict:
        """
        MARK 階段
        
        標記結構中的關鍵點
        """
        marked = structured.copy()
        
        # 生成唯一標記
        mark_id = hashlib.md5(json.dumps(structured, sort_keys=True, default=str).encode()).hexdigest()[:8]
        marked['mark_id'] = mark_id
        marked['mark_time'] = datetime.utcnow().isoformat()
        
        # 記錄到索引
        self.mark_index[mark_id] = marked
        
        return marked
    
    def flow(self, marked: Dict) -> Dict:
        """
        FLOW 階段
        
        建立流動關係
        """
        flowed = marked.copy()
        
        # 建立與其他已標記結構的關聯
        connections = []
        for other_id, other_marked in self.mark_index.items():
            if other_id != marked.get('mark_id'):
                # 計算相似度
                if 'simhash' in marked and 'simhash' in other_marked:
                    similarity = SimHash64.similarity(marked['simhash'], other_marked['simhash'])
                    if similarity > 0.5:
                        connections.append({
                            'target': other_id,
                            'similarity': similarity
                        })
        
        flowed['connections'] = connections
        
        # 更新流圖
        mark_id = marked.get('mark_id')
        if mark_id:
            self.flow_graph[mark_id] = [c['target'] for c in connections]
        
        return flowed
    
    def recurse(self, flowed: Dict, depth: int = 0, max_depth: int = 3) -> Dict:
        """
        RECURSE 階段
        
        遞歸處理子結構
        """
        if depth >= max_depth:
            return flowed
        
        recursed = flowed.copy()
        recursed['recurse_depth'] = depth
        
        # 遞歸處理內容
        if 'content' in recursed:
            content = recursed['content']
            if isinstance(content, dict):
                recursed['sub_seeds'] = {}
                for key, value in content.items():
                    if isinstance(value, (dict, list, str)) and len(str(value)) > 10:
                        sub_seed = self.extract(value, max_depth=max_depth - depth - 1)
                        recursed['sub_seeds'][key] = sub_seed
            elif isinstance(content, list):
                recursed['sub_seeds'] = []
                for i, item in enumerate(content[:10]):  # 限制數量
                    if isinstance(item, (dict, list, str)) and len(str(item)) > 10:
                        sub_seed = self.extract(item, max_depth=max_depth - depth - 1)
                        recursed['sub_seeds'].append(sub_seed)
        
        return recursed
    
    def store(self, recursed: Dict) -> Dict:
        """
        STORE 階段
        
        存儲到 Merkle Chain
        """
        stored = recursed.copy()
        
        # 序列化並存儲
        serialized = json.dumps(recursed, sort_keys=True, default=str)
        node = self.storage.add(serialized)
        
        stored['storage'] = {
            'hash': node.hash,
            'timestamp': node.timestamp,
            'merkle_root': self.storage.get_root_hash()
        }
        
        return stored
    
    def extract(self, x: Any, max_depth: int = 3) -> Dict:
        """
        完整的 SEED 萃取流程
        
        SEED(X) = STORE(RECURSE(FLOW(MARK(STRUCTURE(X)))))
        """
        structured = self.structure(x)
        marked = self.mark(structured)
        flowed = self.flow(marked)
        recursed = self.recurse(flowed, max_depth=max_depth)
        stored = self.store(recursed)
        
        return stored


# ============================================
# 第七部分：智能倉庫同步系統（主入口）
# ============================================

class IntelligentRepoSync:
    """
    智能倉庫同步系統
    
    整合所有組件的主系統
    """
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.scanner = GlobalSemanticScanner()
        self.seed_extractor = SEEDExtractor()
        self.attention = ParticleAttention()
        self.sync_history: List[Dict] = []
    
    def analyze_repo(self, repo_path: str, repo_name: str = None) -> Dict:
        """分析單個倉庫"""
        print(f"🔍 Scanning repository: {repo_path}")
        
        structure = self.scanner.scan_repository(repo_path, repo_name)
        
        # 萃取核心種子
        seed = self.seed_extractor.extract(structure)
        
        # 使用注意力機制找出最重要的部分
        if structure['total_concepts']:
            concept_graph = self._build_concept_graph(structure)
            self.attention.run_cycle(structure['total_concepts'][0], concept_graph)
            top_concepts = self.attention.get_top_k(10)
            structure['key_concepts'] = [c[0] for c in top_concepts]
        
        result = {
            'structure': structure,
            'seed': seed,
            'attention_state': self.attention.to_memory_particle()
        }
        
        self.sync_history.append({
            'action': 'analyze',
            'repo': repo_name or repo_path,
            'time': datetime.utcnow().isoformat()
        })
        
        return result
    
    def _build_concept_graph(self, structure: Dict) -> Dict[str, List[str]]:
        """從結構中構建概念圖"""
        graph = defaultdict(list)
        concepts = structure.get('total_concepts', [])
        
        # 簡單的共現關係
        for file_struct in structure.get('files', []):
            file_concepts = file_struct.get('concepts', [])
            for i, c1 in enumerate(file_concepts):
                for c2 in file_concepts[i+1:]:
                    graph[c1].append(c2)
                    graph[c2].append(c1)
        
        return dict(graph)
    
    def sync_repos(self, repo_paths: List[str]) -> Dict:
        """同步多個倉庫"""
        print(f"🔄 Syncing {len(repo_paths)} repositories...")
        
        results = {}
        for path in repo_paths:
            name = Path(path).name
            results[name] = self.analyze_repo(path, name)
        
        # 查找跨倉庫關聯
        cross_relations = self.scanner.find_cross_repo_relations()
        
        sync_result = {
            'repos': results,
            'cross_relations': cross_relations,
            'report': self.scanner.generate_report(),
            'sync_time': datetime.utcnow().isoformat()
        }
        
        self.sync_history.append({
            'action': 'sync',
            'repos': [Path(p).name for p in repo_paths],
            'time': datetime.utcnow().isoformat()
        })
        
        return sync_result
    
    def export_report(self, output_path: str, format: str = 'json') -> str:
        """導出報告"""
        report = self.scanner.generate_report()
        report['sync_history'] = self.sync_history
        
        output = Path(output_path)
        
        if format == 'json':
            with open(output, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False, default=str)
        elif format == 'md':
            md_content = self._generate_markdown_report(report)
            with open(output, 'w', encoding='utf-8') as f:
                f.write(md_content)
        
        print(f"📄 Report exported to: {output}")
        return str(output)
    
    def _generate_markdown_report(self, report: Dict) -> str:
        """生成 Markdown 格式報告"""
        lines = [
            "# 智能倉庫同步報告",
            "",
            f"生成時間: {report.get('generated_at', 'N/A')}",
            "",
            "## 概覽",
            "",
            f"- 掃描倉庫數: {report['scan_summary']['total_repos']}",
            f"- 總文件數: {report['scan_summary']['total_files']}",
            f"- Merkle Root: `{report['scan_summary']['merkle_root']}`",
            "",
            "## 倉庫詳情",
            ""
        ]
        
        for repo_name, repo_data in report.get('repositories', {}).items():
            lines.extend([
                f"### {repo_name}",
                "",
                f"- 文件數: {len(repo_data.get('files', []))}",
                f"- 概念數: {len(repo_data.get('total_concepts', []))}",
                f"- 架構模式: {', '.join(repo_data.get('total_patterns', {}).keys())}",
                ""
            ])
            
            if repo_data.get('key_concepts'):
                lines.append(f"**關鍵概念**: {', '.join(repo_data['key_concepts'][:10])}")
                lines.append("")
        
        if report.get('cross_repo_relations'):
            lines.extend([
                "## 跨倉庫關聯",
                ""
            ])
            for rel in report['cross_repo_relations']:
                lines.append(f"- **{rel['repo1']}** ↔ **{rel['repo2']}**: {rel['type']} ({len(rel['items'])} items)")
            lines.append("")
        
        lines.extend([
            "---",
            "",
            "*Generated by MrLiouWord Intelligent Repo Sync System*",
            "",
            "*怎麼過去，就怎麼回來*"
        ])
        
        return '\n'.join(lines)


# ============================================
# CLI 入口
# ============================================

def main():
    """命令行入口"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='智能倉庫同步系統 - MrLiouWord Particle System',
        epilog='怎麼過去，就怎麼回來'
    )
    
    parser.add_argument('action', choices=['scan', 'sync', 'analyze'],
                       help='執行的操作')
    parser.add_argument('paths', nargs='+', help='倉庫路徑')
    parser.add_argument('-o', '--output', default='repo_report.json',
                       help='輸出文件路徑')
    parser.add_argument('-f', '--format', choices=['json', 'md'], default='json',
                       help='輸出格式')
    parser.add_argument('-v', '--verbose', action='store_true',
                       help='詳細輸出')
    
    args = parser.parse_args()
    
    sync = IntelligentRepoSync()
    
    if args.action == 'scan':
        for path in args.paths:
            result = sync.analyze_repo(path)
            if args.verbose:
                print(json.dumps(result['structure'], indent=2, ensure_ascii=False, default=str))
    
    elif args.action == 'sync':
        result = sync.sync_repos(args.paths)
        if args.verbose:
            print(json.dumps(result['report'], indent=2, ensure_ascii=False, default=str))
    
    elif args.action == 'analyze':
        for path in args.paths:
            result = sync.analyze_repo(path)
            print(f"\n📊 Analysis for {path}:")
            print(f"   Files: {len(result['structure']['files'])}")
            print(f"   Concepts: {len(result['structure']['total_concepts'])}")
            print(f"   Patterns: {list(result['structure']['total_patterns'].keys())}")
            if result['structure'].get('key_concepts'):
                print(f"   Key Concepts: {result['structure']['key_concepts'][:5]}")
    
    # 導出報告
    sync.export_report(args.output, args.format)
    print(f"\n✅ Done! Report saved to {args.output}")


if __name__ == '__main__':
    main()
