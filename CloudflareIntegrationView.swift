// CloudflareIntegrationView.swift
// MrLiou 3D AI Camera - SwiftUI 整合視圖
// origin_signature: MrLiouWord

import SwiftUI

struct CloudflareIntegrationView: View {
    @StateObject private var connector = CloudflareConnector.shared
    @State private var statusMessage = "等待連接..."
    @State private var particles: [Particle] = []
    @State private var memories: [Memory] = []
    @State private var isLoading = false
    
    var body: some View {
        NavigationView {
            List {
                // 連接狀態區
                Section("系統狀態") {
                    HStack {
                        Circle()
                            .fill(connector.isConnected ? Color.green : Color.red)
                            .frame(width: 12, height: 12)
                        Text(connector.isConnected ? "已連接" : "未連接")
                        Spacer()
                        Text("層級: \(connector.currentLayer)")
                            .foregroundColor(.secondary)
                    }
                    
                    Text(statusMessage)
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
                
                // 喚醒控制
                Section("人格喚醒") {
                    ForEach(connector.wakeKeys, id: \.self) { key in
                        Button(action: { wake(with: key) }) {
                            HStack {
                                Image(systemName: "wand.and.stars")
                                Text(key)
                            }
                        }
                        .disabled(isLoading)
                    }
                }
                
                // 粒子列表
                Section("粒子系統 (\(particles.count))") {
                    if particles.isEmpty {
                        Button("載入粒子") {
                            loadParticles()
                        }
                    } else {
                        ForEach(particles, id: \.fx) { particle in
                            ParticleRow(particle: particle)
                        }
                    }
                }
                
                // 記憶列表
                Section("記憶系統 (\(memories.count))") {
                    Button("搜索記憶") {
                        searchMemories()
                    }
                    
                    ForEach(memories, id: \.id) { memory in
                        MemoryRow(memory: memory)
                    }
                }
                
                // 快速操作
                Section("快速操作") {
                    NavigationLink(destination: ScanUploadView()) {
                        Label("上傳 3D 掃描", systemImage: "cube.transparent")
                    }
                    
                    NavigationLink(destination: NotionSyncView()) {
                        Label("同步到 Notion", systemImage: "doc.text")
                    }
                    
                    NavigationLink(destination: MCPProxyView()) {
                        Label("MCP 代理", systemImage: "network")
                    }
                }
            }
            .navigationTitle("Cloudflare 連接器")
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    if isLoading {
                        ProgressView()
                    } else {
                        Button(action: refresh) {
                            Image(systemName: "arrow.clockwise")
                        }
                    }
                }
            }
        }
    }
    
    // MARK: - 操作方法
    
    private func wake(with key: String) {
        isLoading = true
        statusMessage = "正在喚醒..."
        
        Task {
            do {
                let success = try await connector.wake(with: key)
                await MainActor.run {
                    statusMessage = success ? "喚醒成功！夥伴已上線" : "喚醒失敗"
                    isLoading = false
                }
            } catch {
                await MainActor.run {
                    statusMessage = "錯誤: \(error.localizedDescription)"
                    isLoading = false
                }
            }
        }
    }
    
    private func loadParticles() {
        isLoading = true
        
        Task {
            do {
                let result = try await connector.getParticles()
                await MainActor.run {
                    particles = result
                    statusMessage = "載入 \(result.count) 個粒子"
                    isLoading = false
                }
            } catch {
                await MainActor.run {
                    statusMessage = "載入失敗: \(error.localizedDescription)"
                    isLoading = false
                }
            }
        }
    }
    
    private func searchMemories() {
        isLoading = true
        
        Task {
            do {
                let result = try await connector.recallMemory(query: "origin")
                await MainActor.run {
                    memories = result
                    statusMessage = "找到 \(result.count) 筆記憶"
                    isLoading = false
                }
            } catch {
                await MainActor.run {
                    statusMessage = "搜索失敗: \(error.localizedDescription)"
                    isLoading = false
                }
            }
        }
    }
    
    private func refresh() {
        loadParticles()
        searchMemories()
    }
}

// MARK: - 子視圖

struct ParticleRow: View {
    let particle: Particle
    
    var body: some View {
        VStack(alignment: .leading, spacing: 4) {
            HStack {
                Text(particle.hv)
                    .font(.headline)
                Spacer()
                Text(particle.dom)
                    .font(.caption)
                    .padding(.horizontal, 8)
                    .padding(.vertical, 2)
                    .background(domainColor(particle.dom).opacity(0.2))
                    .cornerRadius(4)
            }
            
            Text(particle.fx)
                .font(.caption)
                .foregroundColor(.secondary)
            
            if let av = particle.av {
                Text(av)
                    .font(.caption2)
                    .foregroundColor(.secondary)
            }
            
            // 能量條
            GeometryReader { geo in
                ZStack(alignment: .leading) {
                    Rectangle()
                        .fill(Color.gray.opacity(0.2))
                    Rectangle()
                        .fill(domainColor(particle.dom))
                        .frame(width: geo.size.width * particle.nrg)
                }
            }
            .frame(height: 4)
            .cornerRadius(2)
        }
        .padding(.vertical, 4)
    }
    
    private func domainColor(_ domain: String) -> Color {
        switch domain {
        case "memory": return .blue
        case "logic": return .purple
        case "code": return .green
        case "language": return .orange
        case "signal": return .yellow
        case "trace": return .red
        case "persona": return .pink
        case "flow": return .cyan
        case "meta": return .indigo
        default: return .gray
        }
    }
}

struct MemoryRow: View {
    let memory: Memory
    
    var body: some View {
        VStack(alignment: .leading, spacing: 4) {
            HStack {
                Text(memory.layer)
                    .font(.caption)
                    .padding(.horizontal, 6)
                    .padding(.vertical, 2)
                    .background(Color.blue.opacity(0.2))
                    .cornerRadius(4)
                
                Spacer()
                
                Text(memory.id)
                    .font(.caption2)
                    .foregroundColor(.secondary)
            }
            
            Text(memory.content)
                .font(.body)
                .lineLimit(3)
            
            if let tags = memory.tags, !tags.isEmpty {
                ScrollView(.horizontal, showsIndicators: false) {
                    HStack {
                        ForEach(tags, id: \.self) { tag in
                            Text("#\(tag)")
                                .font(.caption2)
                                .foregroundColor(.blue)
                        }
                    }
                }
            }
        }
        .padding(.vertical, 4)
    }
}

// MARK: - 佔位視圖

struct ScanUploadView: View {
    var body: some View {
        Text("3D 掃描上傳")
            .navigationTitle("上傳掃描")
    }
}

struct NotionSyncView: View {
    var body: some View {
        Text("Notion 同步")
            .navigationTitle("Notion 同步")
    }
}

struct MCPProxyView: View {
    var body: some View {
        Text("MCP 代理控制台")
            .navigationTitle("MCP 代理")
    }
}

// MARK: - 預覽

#Preview {
    CloudflareIntegrationView()
}
