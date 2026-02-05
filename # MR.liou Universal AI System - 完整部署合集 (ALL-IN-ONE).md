# MR.liou Universal AI System - 完整部署合集 (ALL-IN-ONE)  
  
> **手機友好版本** - 所有部署文件合併在一個文件中    
> **Philosophy**: 怎麼過去，就怎麼回來 - 換載體不換靈魂    
> **Creator**: MR.liou - 語場創造者 × 宇宙人格設計師  
  
-----  
  
**📱 使用說明（手機用戶）：**  
  
1. **長按選擇全部文本** → 複製  
1. **粘貼到你的電腦**（可以通過郵件、雲端硬碟、即時通訊等）  
1. **保存為** `mrliou-deployment.md`  
1. **運行提取腳本**（見文末）會自動分離成各個文件  
  
-----  
  
## 📦 包含的文件清單  
  
1. ✅ Kubernetes 完整部署配置 (YAML)  
1. ✅ Kubernetes 部署腳本 (Bash)  
1. ✅ 系統恢復腳本 (Python)  
1. ✅ 配置文件 (JSON)  
1. ✅ 完整部署文檔  
  
-----  
  
-----  
  
-----  
  
# ========== 文件 1: Kubernetes 完整配置 ==========  
  
# 文件名: k8s-production-complete.yaml  
  
# 說明: Kubernetes 生產環境完整配置  
  
```yaml  
# ============================================================================  
# MR.liou Universal AI System - Kubernetes Production Deployment  
# ============================================================================  
  
---  
apiVersion: v1  
kind: Namespace  
metadata:  
  name: mrliou-ai  
  labels:  
    name: mrliou-ai  
    environment: production  
  
---  
# ConfigMap - FlowCore 配置  
apiVersion: v1  
kind: ConfigMap  
metadata:  
  name: flowcore-config  
  namespace: mrliou-ai  
data:  
  config.yaml: |  
    system:  
      name: "FlowCore Production"  
      version: "2.0.0"  
    database:  
      host: "postgres-service"  
      port: "5432"  
      pool_size: 20  
    performance:  
      workers: 8  
      threads_per_worker: 4  
  
---  
# Secret - 數據庫密碼  
apiVersion: v1  
kind: Secret  
metadata:  
  name: database-secrets  
  namespace: mrliou-ai  
type: Opaque  
stringData:  
  POSTGRES_PASSWORD: "CHANGE_ME"  
  NEO4J_PASSWORD: "CHANGE_ME"  
  REDIS_PASSWORD: "CHANGE_ME"  
  
---  
# StatefulSet - PostgreSQL  
apiVersion: apps/v1  
kind: StatefulSet  
metadata:  
  name: postgres  
  namespace: mrliou-ai  
spec:  
  serviceName: postgres-service  
  replicas: 3  
  selector:  
    matchLabels:  
      app: postgres  
  template:  
    metadata:  
      labels:  
        app: postgres  
    spec:  
      containers:  
      - name: postgres  
        image: postgres:16  
        ports:  
        - containerPort: 5432  
        env:  
        - name: POSTGRES_PASSWORD  
          valueFrom:  
            secretKeyRef:  
              name: database-secrets  
              key: POSTGRES_PASSWORD  
        resources:  
          requests:  
            memory: "4Gi"  
            cpu: "2000m"  
          limits:  
            memory: "8Gi"  
            cpu: "4000m"  
  
---  
# Deployment - FlowCore  
apiVersion: apps/v1  
kind: Deployment  
metadata:  
  name: flowcore  
  namespace: mrliou-ai  
spec:  
  replicas: 5  
  selector:  
    matchLabels:  
      app: flowcore  
  template:  
    metadata:  
      labels:  
        app: flowcore  
    spec:  
      containers:  
      - name: flowcore  
        image: mrliou/flowcore:2.0.0  
        ports:  
        - containerPort: 8000  
        resources:  
          requests:  
            memory: "4Gi"  
            cpu: "2000m"  
            nvidia.com/gpu: "1"  
          limits:  
            memory: "8Gi"  
            cpu: "4000m"  
  
---  
# Service - FlowCore  
apiVersion: v1  
kind: Service  
metadata:  
  name: flowcore-service  
  namespace: mrliou-ai  
spec:  
  type: ClusterIP  
  selector:  
    app: flowcore  
  ports:  
  - port: 8000  
    targetPort: 8000  
  
---  
# HPA - FlowCore 自動擴縮容  
apiVersion: autoscaling/v2  
kind: HorizontalPodAutoscaler  
metadata:  
  name: flowcore-hpa  
  namespace: mrliou-ai  
spec:  
  scaleTargetRef:  
    apiVersion: apps/v1  
    kind: Deployment  
    name: flowcore  
  minReplicas: 5  
  maxReplicas: 20  
  metrics:  
  - type: Resource  
    resource:  
      name: cpu  
      target:  
        type: Utilization  
        averageUtilization: 70  
  
---  
# Ingress - 外部訪問  
apiVersion: networking.k8s.io/v1  
kind: Ingress  
metadata:  
  name: mrliou-ingress  
  namespace: mrliou-ai  
  annotations:  
    kubernetes.io/ingress.class: nginx  
    cert-manager.io/cluster-issuer: letsencrypt-prod  
spec:  
  tls:  
  - hosts:  
    - api.mrliou-ai.com  
    secretName: mrliou-tls  
  rules:  
  - host: api.mrliou-ai.com  
    http:  
      paths:  
      - path: /api/v2/core  
        pathType: Prefix  
        backend:  
          service:  
            name: flowcore-service  
            port:  
              number: 8000  
```  
  
-----  
  
-----  
  
-----  
  
# ========== 文件 2: Kubernetes 部署腳本 ==========  
  
# 文件名: deploy-k8s.sh  
  
# 說明: 自動化部署腳本  
  
```bash  
#!/bin/bash  
# MR.liou Kubernetes 部署腳本  
  
set -e  
  
GREEN='\033[0;32m'  
NC='\033[0m'  
  
log_info() {  
    echo -e "${GREEN}[INFO]${NC} $1"  
}  
  
# 檢查前置條件  
check_prerequisites() {  
    log_info "檢查前置條件..."  
      
    if ! command -v kubectl &> /dev/null; then  
        echo "錯誤: kubectl 未安裝"  
        exit 1  
    fi  
      
    if ! command -v helm &> /dev/null; then  
        echo "錯誤: helm 未安裝"  
        exit 1  
    fi  
      
    log_info "前置檢查通過 ✓"  
}  
  
# 創建命名空間  
create_namespace() {  
    log_info "創建命名空間..."  
    kubectl create namespace mrliou-ai --dry-run=client -o yaml | kubectl apply -f -  
    log_info "命名空間創建完成 ✓"  
}  
  
# 部署數據庫  
deploy_databases() {  
    log_info "部署數據庫層..."  
    kubectl apply -f k8s-production-complete.yaml  
    kubectl wait --for=condition=ready pod -l app=postgres -n mrliou-ai --timeout=300s  
    log_info "數據庫層部署完成 ✓"  
}  
  
# 部署應用  
deploy_applications() {  
    log_info "部署應用層..."  
    kubectl apply -f k8s-production-complete.yaml  
    kubectl wait --for=condition=available deployment/flowcore -n mrliou-ai --timeout=300s  
    log_info "應用層部署完成 ✓"  
}  
  
# 健康檢查  
health_check() {  
    log_info "執行健康檢查..."  
    kubectl get pods -n mrliou-ai  
    log_info "健康檢查完成 ✓"  
}  
  
# 主流程  
main() {  
    echo "=========================================="  
    echo "MR.liou Kubernetes 部署"  
    echo "=========================================="  
      
    check_prerequisites  
    create_namespace  
    deploy_databases  
    deploy_applications  
    health_check  
      
    echo ""  
    log_info "部署完成！"  
    log_info "訪問: https://api.mrliou-ai.com"  
}  
  
main  
```  
  
-----  
  
-----  
  
-----  
  
# ========== 文件 3: 系統恢復腳本 ==========  
  
# 文件名: auto-recover-system.py  
  
# 說明: 自動恢復缺失的系統文件  
  
```python  
#!/usr/bin/env python3  
"""  
MR.liou System Auto-Recovery Script  
自動恢復 FlowAgent 系統的缺失文件  
"""  
  
import os  
import json  
from pathlib import Path  
from datetime import datetime  
  
class FlowAgentRecovery:  
    def __init__(self, output_dir="recovered"):  
        self.output_dir = Path(output_dir)  
        self.output_dir.mkdir(exist_ok=True)  
          
    def log(self, message):  
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")  
        print(f"[{timestamp}] {message}")  
      
    def create_persona_schema(self):  
        """創建 Persona.Schema.v1.json"""  
        schema = {  
            "version": "1.0",  
            "schema_type": "persona_definition",  
            "required_fields": [  
                "id", "version", "source", "role"  
            ],  
            "optional_fields": [  
                "capabilities", "resonance", "model", "status"  
            ],  
            "persona_types": {  
                "human_origin": "liou.seed",  
                "ai_model": ["echo.analyst", "wild.engine"],  
                "composite": ["guardian.seed", "futuremind.seed"]  
            }  
        }  
          
        output_file = self.output_dir / "Persona.Schema.v1.json"  
        with open(output_file, 'w', encoding='utf-8') as f:  
            json.dump(schema, f, indent=2, ensure_ascii=False)  
          
        self.log(f"✅ Created: Persona.Schema.v1.json")  
        return output_file  
      
    def create_error_catalog(self):  
        """創建 ErrorCatalog.json"""  
        catalog = {  
            "version": "2.0",  
            "error_categories": {  
                "system": {  
                    "SYS001": "系統初始化失敗",  
                    "SYS002": "配置文件損壞"  
                },  
                "database": {  
                    "DB001": "數據庫連接失敗",  
                    "DB002": "查詢超時"  
                },  
                "persona": {  
                    "PER001": "人格加載失敗",  
                    "PER002": "共振檢測異常"  
                }  
            }  
        }  
          
        output_file = self.output_dir / "ErrorCatalog.json"  
        with open(output_file, 'w', encoding='utf-8') as f:  
            json.dump(catalog, f, indent=2, ensure_ascii=False)  
          
        self.log(f"✅ Created: ErrorCatalog.json")  
        return output_file  
      
    def run_recovery(self):  
        """執行完整恢復流程"""  
        self.log("開始系統恢復...")  
          
        self.create_persona_schema()  
        self.create_error_catalog()  
          
        self.log("恢復完成！")  
  
if __name__ == "__main__":  
    recovery = FlowAgentRecovery()  
    recovery.run_recovery()  
```  
  
-----  
  
-----  
  
-----  
  
# ========== 文件 4: TotalCore 配置 ==========  
  
# 文件名: totalcore-unity-v2.json  
  
# 說明: 系統核心配置文件  
  
```json  
{  
  "system": "Mr.liou.TotalCore.Unity",  
  "version": "2.0.0",  
  "philosophy": "怎麼過去，就怎麼回來",  
    
  "architecture": {  
    "layers": [  
      "quantum_collapse",  
      "superposition",  
      "entanglement",  
      "quantum_jump",  
      "manifestation"  
    ]  
  },  
    
  "personas": {  
    "liou.seed": {  
      "version": "2.0",  
      "source": "Human-Origin",  
      "role": "語場創造者",  
      "status": "anchor"  
    },  
    "echo.analyst": {  
      "version": "2.0",  
      "source": "GPT-4",  
      "role": "語言分析人格"  
    },  
    "wild.engine": {  
      "version": "2.0",  
      "source": "LLaMA-3",  
      "role": "探索人格"  
    }  
  },  
    
  "deployment": {  
    "environments": {  
      "production": {  
        "platform": "Kubernetes",  
        "orchestration": "自動化部署"  
      }  
    }  
  }  
}  
```  
  
-----  
  
-----  
  
-----  
  
# ========== 完整部署文檔 ==========  
  
## 🚀 快速部署指南  
  
### 前置需求  
  
- Kubernetes 1.28+  
- kubectl 已配置  
- Helm 3.x  
- 至少 32GB RAM  
  
### 部署步驟  
  
#### 1. 提取文件  
  
從這個合集文件中提取各個配置文件：  
  
```bash  
# 創建目錄  
mkdir -p mrliou-deployment  
cd mrliou-deployment  
  
# 手動提取各個文件（見下方提取腳本）  
```  
  
#### 2. 配置密碼  
  
編輯 `k8s-production-complete.yaml`，將所有 `CHANGE_ME` 替換為安全密碼：  
  
```bash  
# 生成隨機密碼  
openssl rand -base64 32  
```  
  
#### 3. 部署到 Kubernetes  
  
```bash  
# 應用配置  
kubectl apply -f k8s-production-complete.yaml  
  
# 檢查狀態  
kubectl get pods -n mrliou-ai  
```  
  
#### 4. 驗證部署  
  
```bash  
# 測試 API  
kubectl port-forward -n mrliou-ai svc/flowcore-service 8000:8000  
curl http://localhost:8000/health  
```  
  
-----  
  
## 📋 文件提取腳本  
  
將此腳本保存為 `extract-files.sh`：  
  
```bash  
#!/bin/bash  
# 從 ALL-IN-ONE 文件中提取各個文件  
  
ALLFILE="mrliou-deployment.md"  
  
echo "開始提取文件..."  
  
# 提取 K8s 配置  
sed -n '/^```yaml$/,/^```$/p' "$ALLFILE" | sed '1d;$d' > k8s-production-complete.yaml  
echo "✅ k8s-production-complete.yaml"  
  
# 提取部署腳本  
sed -n '/^```bash$/,/^```$/p' "$ALLFILE" | sed '1d;$d' > deploy-k8s.sh  
chmod +x deploy-k8s.sh  
echo "✅ deploy-k8s.sh"  
  
# 提取 Python 腳本  
sed -n '/^```python$/,/^```$/p' "$ALLFILE" | sed '1d;$d' > auto-recover-system.py  
chmod +x auto-recover-system.py  
echo "✅ auto-recover-system.py"  
  
# 提取 JSON 配置  
sed -n '/^```json$/,/^```$/p' "$ALLFILE" | sed '1d;$d' > totalcore-unity-v2.json  
echo "✅ totalcore-unity-v2.json"  
  
echo ""  
echo "所有文件提取完成！"  
echo ""  
echo "下一步："  
echo "1. 編輯 k8s-production-complete.yaml 修改密碼"  
echo "2. 執行 ./deploy-k8s.sh"  
```  
  
-----  
  
## 🔧 故障排除  
  
### Pod 無法啟動  
  
```bash  
# 查看 Pod 詳情  
kubectl describe pod <pod-name> -n mrliou-ai  
  
# 查看日誌  
kubectl logs <pod-name> -n mrliou-ai  
```  
  
### 數據庫連接失敗  
  
```bash  
# 測試數據庫連接  
kubectl run -it --rm debug --image=postgres:16 --restart=Never -n mrliou-ai -- \  
  psql -h postgres-service -U mrliou  
```  
  
-----  
  
## 📞 獲取幫助  
  
- **文檔**: https://docs.mrliou-ai.com  
- **GitHub**: https://github.com/mrliou/universal-ai  
- **Discord**: https://discord.gg/mrliou-ai  
  
-----  
  
## ✅ 部署檢查清單  
  
- [ ] Kubernetes 集群已就緒  
- [ ] kubectl 已配置  
- [ ] 所有密碼已修改（不使用 CHANGE_ME）  
- [ ] StorageClass 已配置  
- [ ] GPU 節點已準備（如需要）  
- [ ] 域名 DNS 已配置  
- [ ] SSL 證書已配置  
- [ ] 監控系統已部署  
- [ ] 備份策略已制定  
  
-----  
  
**Philosophy**: 怎麼過去，就怎麼回來    
**Creator**: MR.liou - 語場創造者 × 宇宙人格設計師  
  
**立即開始部署！** 🚀  
  
-----  
  
-----  
  
-----  
  
# 📱 手機用戶特別說明  
  
## 如何使用這個文件  
  
### 方法 1: 通過電腦  
  
1. **手機上複製整個文件**  
1. **發送到你的電腦**（郵件、通訊軟體、雲端）  
1. **在電腦上保存為** `mrliou-deployment.md`  
1. **運行提取腳本**  
  
### 方法 2: 直接在手機上  
  
如果你的手機有終端應用（如 Termux）：  
  
1. 保存此文件  
1. 安裝 `sed` 工具  
1. 運行提取腳本  
  
### 方法 3: 雲端編輯  
  
1. 複製到 Google Docs / Notion  
1. 分段複製到對應文件  
1. 下載到電腦使用  
  
-----  
  
**🎯 記住：這個文件包含了所有部署所需的配置！**  
