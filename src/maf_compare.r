library(maftools)
args = commandArgs(trailingOnly=TRUE)

maf1 = readRDS(sprintf('C:/Users/Eric Jiang/Documents/Spring2020/DSC180B/studies/%s.rds', args[1]))
maf2 = readRDS(sprintf('C:/Users/Eric Jiang/Documents/Spring2020/DSC180B/studies/%s.rds', args[2]))
threshold = mafCompare(maf1, maf2)[[1]][adjPval < 0.0001]
write.table(threshold, file=sprintf("C:/Users/Eric Jiang/Documents/Spring2020/DSC180B/studies/%s_vs_%s.csv", args[1], args[2]))